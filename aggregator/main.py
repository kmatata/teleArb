import os
import signal
import sys
from commands.monitor_exports import DirectoryWatcher
from utils.logger import Logger
from get_env_vars import load_environment_variables

load_environment_variables()

# Configure paths
EXPORTS_PATH = os.getenv("EXPORTS_PATH", "~/exports")
MONITOR_DB_PATH = os.path.expanduser(
    os.getenv("MONITOR_DB_PATH", "./monitorDB/monitor.db")
)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "sql/monitor.sql")

logger = Logger(__name__)


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutting down monitor gracefully...")
    if hasattr(signal_handler, "watcher") and signal_handler.watcher.is_running:
        signal_handler.watcher.stop()
        sys.exit(0)


def main():
    try:
        # signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        test_mode = os.getenv("MONITOR_TEST", "").lower() == "true"
        # init n start watcher
        watcher = DirectoryWatcher(
            watch_path=EXPORTS_PATH,
            db_path=MONITOR_DB_PATH,
            schema_path=SCHEMA_PATH,
            cleanup_interval=5,
            test_mode=test_mode,
        )

        # store watcher ref for signal handler
        signal_handler.watcher = watcher

        logger.info("Starting export monitoring...")
        watcher.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt in main...")
        if "watcher" in locals():
            watcher.stop()
    except Exception as e:
        logger.critical(f"Fatal error in monitor: {str(e)}")
        sys.exit(1)
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
