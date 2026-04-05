"""
OMOP CDM 5.4 DDL migration script for PostgreSQL.
Applies the OMOP CDM schema to the target database.

Usage:
    python -m src.omop.ddl.migrate --dbname omop_cdm --user integrum_user --password integrum_password --host localhost --port 5432
"""

import argparse
import asyncio
import sys
from pathlib import Path

import asyncpg

DDL_FILE = Path(__file__).parent / "omop_cdm_5.4_postgresql.sql"


async def run_migration(
    dbname: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
):
    """Apply OMOP CDM DDL to the target database."""
    conn = await asyncpg.connect(
        database=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

    try:
        ddl = DDL_FILE.read_text()

        # Split by semicolons and execute each statement
        statements = [
            s.strip()
            for s in ddl.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        executed = 0
        for stmt in statements:
            # Skip pure comment blocks
            if stmt.startswith("--"):
                continue
            try:
                await conn.execute(stmt)
                executed += 1
            except asyncpg.exceptions.DuplicateTableError:
                pass  # Table already exists, which is fine
            except Exception as e:
                print(f"Warning: {e}")
                print(f"Statement: {stmt[:100]}...")

        print(f"OMOP CDM 5.4 migration complete. {executed} statements executed.")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Apply OMOP CDM 5.4 DDL to PostgreSQL")
    parser.add_argument("--dbname", required=True, help="Database name")
    parser.add_argument("--user", required=True, help="Database user")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    args = parser.parse_args()

    asyncio.run(
        run_migration(
            dbname=args.dbname,
            user=args.user,
            password=args.password,
            host=args.host,
            port=args.port,
        )
    )


if __name__ == "__main__":
    main()
