import os
import time
from pathlib import Path
from typing import Set
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from utils.db_manager import MonitorDatabaseManager
from utils.logger import Logger
import sqlite3


class DirectoryWatcherHandler(FileSystemEventHandler):
    """Handles file system events for new database exports"""

    def __init__(self, db_manager: MonitorDatabaseManager, logger: Logger):
        self.db_manager = db_manager
        self.logger = logger
        self._processing_files: Set[str] = set()
        self._lock = threading.Lock()

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle new file creation events"""
        if not event.is_directory and event.src_path.endswith(".db"):
            with self._lock:
                if event.src_path not in self._processing_files:
                    self._processing_files.add(event.src_path)
                    self._process_file(event.src_path)

    def _process_file(self, file_path: str) -> None:
        """Process a single export database file"""
        try:
            self.logger.info(f"Processing export file: {file_path}")

            # is file ready for reading
            if not self._wait_for_file_ready(file_path):
                self.logger.error(f"File not ready for processing: {file_path}")
                return

            # Process the export database
            if self.db_manager.process_export_db(Path(file_path)):
                # Run cleanup rules after successful processing
                # self.db_manager.clean_old_records()

                try:
                    os.remove(file_path)
                    self.logger.info(f"Successfully processed and removed: {file_path}")
                except OSError as e:
                    self.logger.error(f"Failed to remove file {file_path}: {str(e)}")
            else:
                self.logger.error(f"Failed to process export file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")

    def _wait_for_file_ready(self, file_path: str, timeout: int = 5) -> bool:
        """
        Wait for file to be completely written and ready for processing
        Returns: True if file is ready, False if timeout or error
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with sqlite3.connect(file_path) as conn:
                    cursor = conn.cursor()
                    # Check if our target table exists
                    cursor.execute(
                        """
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='match_arbitrage_export'
                    """
                    )
                    if cursor.fetchone():
                        return True
                time.sleep(0.1)
            except (IOError, PermissionError):
                time.sleep(0.1)
                continue
        return False


class DirectoryWatcher:
    """Monitors export directory for new database files"""

    def __init__(
        self,
        watch_path: str,
        db_path: str,
        schema_path: str,
        cleanup_interval: int = 5,
        test_mode: bool = False,  # test mode flag
    ):
        self.watch_path = Path(watch_path).expanduser()
        self.logger = Logger(__name__)
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self.test_mode = test_mode

        # init monitor db
        self.db_manager = MonitorDatabaseManager(db_path, schema_path)

        # init watchdog handler
        self.event_handler = DirectoryWatcherHandler(self.db_manager, self.logger)
        self.observer = Observer()
        self.observer.daemon = True
        self.observer.schedule(
            self.event_handler, str(self.watch_path), recursive=False
        )

        # running state track
        self._running = False
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start directory monitoring"""
        try:
            self.logger.info(f"Starting directory monitoring on: {self.watch_path}")
            self._running = True
            self.observer.start()

            if self.test_mode:
                self._process_single_file()
                self.stop()
                return

            self._process_existing_files()

            # main monitor loop
            while not self._stop_event.is_set():
                try:

                    current_time = time.time()
                    if current_time - self.last_cleanup > self.cleanup_interval:
                        # self.db_manager.clean_old_records()
                        self.last_cleanup = current_time
                    
                    time.sleep(0.5)

                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt...")
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {str(e)}")
                    if not self._running:
                        break
                    continue

        except Exception as e:
            self.logger.error(f"Failed to start directory monitoring: {str(e)}")
        finally:
            self._running = False
            self.stop()

    def stop(self) -> None:
        """Stop directory monitoring"""
        try:
            self.logger.info("Stopping directory monitoring")
            self._stop_event.set()

            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5)

            self.observer.stop()
            self.observer.join()
            self._running = False
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            self._running = False

    def _process_existing_files(self) -> None:
        """Process any existing .db files in the watch directory"""
        try:
            for file_path in self.watch_path.glob("*.db"):
                self.event_handler._process_file(str(file_path))
        except Exception as e:
            self.logger.error(f"Error processing existing files: {str(e)}")

    def _process_single_file(self) -> None:
        """Process single file for test mode"""
        try:
            # first .db file in dir
            db_files = list(self.watch_path.glob("*.db"))
            if db_files:
                self.logger.info("Test mode: processing single file")
                self.event_handler._process_file(str(db_files[0]))
            else:
                self.logger.info("Test mode: no files to process")
        except Exception as e:
            self.logger.error(f"Error processing test file: {str(e)}")

    @property
    def is_running(self) -> bool:
        """Check if watcher is currently running"""
        return self._running
