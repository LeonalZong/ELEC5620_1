"""
One-off schema migration to make reports.stock_id nullable.

Usage:
  source venv/bin/activate
  python stock-analysis-system/scripts/migrate_reports_nullable.py

It will read DATABASE_URL from app.config.Settings (and .env if present),
connect to the DB and execute ALTER TABLE.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sqlalchemy import create_engine, text
from app.config import settings


def main():
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE reports MODIFY stock_id INT NULL"))
    print("✅ reports.stock_id set to NULLABLE")


if __name__ == "__main__":
    main()


