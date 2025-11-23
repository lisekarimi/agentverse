# src/prism/database.py
"""Database connection, schema, and seed data for PRISM."""
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

# Database Schema
SCHEMA_SQL = """
-- Create positions table
CREATE TABLE IF NOT EXISTS swap_positions (
    position_id VARCHAR(50) PRIMARY KEY,
    trade_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    notional DECIMAL(15,2) NOT NULL,
    fixed_rate DECIMAL(6,4) NOT NULL,
    float_index VARCHAR(20) NOT NULL,
    pay_receive VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create market rates table
CREATE TABLE IF NOT EXISTS market_rates (
    rate_id SERIAL PRIMARY KEY,
    tenor VARCHAR(10) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    mid_rate DECIMAL(6,4) NOT NULL,
    bid_rate DECIMAL(6,4),
    ask_rate DECIMAL(6,4),
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50)
);

-- Create trade signals table
CREATE TABLE IF NOT EXISTS trade_signals (
    signal_id SERIAL PRIMARY KEY,
    position_id VARCHAR(50),
    signal_type VARCHAR(20),
    reason TEXT,
    current_pnl DECIMAL(15,2),
    recommended_action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (position_id) REFERENCES swap_positions(position_id)
);

-- Create demo executions table for rate limiting
CREATE TABLE IF NOT EXISTS demo_executions (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    last_run TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ip_time ON demo_executions(ip_address, last_run);
"""


class DatabaseConnection:
    """Manages database connections and query execution."""

    def __init__(self):
        """Initialize database connection manager."""
        self.database_url = os.getenv("DATABASE_URL")
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                self.database_url, cursor_factory=RealDictCursor
            )
            return self.conn
        except Exception:
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=None):
        """Execute a query and return results."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                return results
            else:
                self.conn.commit()
                rowcount = cursor.rowcount
                return rowcount
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def initialize_schema(self):
        """Initialize database schema from SQL string."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(SCHEMA_SQL)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()


def initialize_database():
    """Initialize the database with schema."""
    db = DatabaseConnection()
    db.connect()
    db.initialize_schema()
    db.close()
    # Seed initial data
    seed_positions()


def seed_positions():
    """Insert sample swap positions for testing."""
    db = DatabaseConnection()
    db.connect()

    # Sample positions
    positions = [
        (
            "SWP001",
            "2024-01-15",
            "2029-01-15",
            10000000,
            4.25,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP002",
            "2024-03-20",
            "2034-03-20",
            25000000,
            4.50,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
        (
            "SWP003",
            "2024-06-10",
            "2029-06-10",
            15000000,
            4.10,
            "SOFR",
            "PAY_FIXED",
            "USD",
        ),
        (
            "SWP004",
            "2024-08-05",
            "2027-08-05",
            8000000,
            3.95,
            "SOFR",
            "RCV_FIXED",
            "USD",
        ),
    ]

    insert_query = """
        INSERT INTO swap_positions
        (position_id, trade_date, maturity_date, notional, fixed_rate, float_index, pay_receive, currency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (position_id) DO NOTHING
    """

    for position in positions:
        db.execute_query(insert_query, position)

    db.close()
    print(f"✅ Seeded {len(positions)} swap positions!")
