CREATE TABLE
    IF NOT EXISTS match_arbitrage_aggregate (
        match_id INTEGER,
        arbitrage_id INTEGER NOT NULL,
        home_team_id INTEGER,
        away_team_id INTEGER,
        competition_id INTEGER,
        home_team_name TEXT,
        away_team_name TEXT,
        competition_name TEXT,
        competition_country TEXT,
        market_type TEXT NOT NULL,
        data_source TEXT NOT NULL,
        bet_description TEXT NOT NULL,
        bookmaker_odd_key1 TEXT NOT NULL,
        bookmaker_odd_key2 TEXT NOT NULL,
        bookmaker_odd_key3 TEXT NULL,
        start_time TIMESTAMP,
        match_date DATE,
        total_stake DECIMAL(10, 2),
        min_guaranteed_profit DECIMAL(10, 2),
        max_guaranteed_profit DECIMAL(10, 2),
        arbitrage_created TIMESTAMP,
        arbitrage_updated TIMESTAMP,
        three_way_market_data JSON,
        btts_market_data JSON,
        three_way_odds_data JSON,
        btts_odds_data JSON,
        PRIMARY KEY (match_id, arbitrage_id)
    );

CREATE INDEX IF NOT EXISTS idx_arbitrage_id ON match_arbitrage_aggregate (arbitrage_id);

CREATE INDEX IF NOT EXISTS idx_market_type ON match_arbitrage_aggregate (market_type);

CREATE INDEX IF NOT EXISTS idx_data_source ON match_arbitrage_aggregate (data_source);

CREATE INDEX IF NOT EXISTS idx_bet_description ON match_arbitrage_aggregate (bet_description);

CREATE INDEX IF NOT EXISTS idx_timestamps ON match_arbitrage_aggregate (arbitrage_created, arbitrage_updated);