import argparse
import hashlib
import os
import sys
import time
from pathlib import Path
from typing import Iterable, List

import mysql.connector
from mysql.connector import Error
import sqlparse


def log(message: str) -> None:
    print(f"[migrator] {message}", flush=True)


def env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    if value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def checksum_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def connect_with_retry(config: dict, retries: int = 30, delay_seconds: int = 2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(**config)
            if conn.is_connected():
                return conn
        except Error as err:
            last_error = err
            log(f"DB not ready yet (attempt {attempt}/{retries}): {err}")
            time.sleep(delay_seconds)
    raise RuntimeError(f"Failed to connect after {retries} attempts: {last_error}")


def ensure_database(host: str, port: int, user: str, password: str, database: str, allow_create: bool) -> None:
    if not allow_create:
        log("MYSQL_CREATE_DATABASE=false, skipping CREATE DATABASE step.")
        return

    config = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "autocommit": True,
    }
    conn = connect_with_retry(config)
    try:
        with conn.cursor() as cursor:
            sql = (
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "DEFAULT COLLATE utf8mb4_0900_ai_ci"
            )
            cursor.execute(sql)
            log(f"Ensured database exists: {database}")
    finally:
        conn.close()


def ensure_schema_migrations_table(conn) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      filename VARCHAR(255) NOT NULL,
      checksum CHAR(64) NOT NULL,
      applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      success TINYINT(1) NOT NULL DEFAULT 1,
      PRIMARY KEY (id),
      UNIQUE KEY uq_schema_migrations_file_checksum (filename, checksum)
    ) ENGINE=InnoDB
    """
    with conn.cursor() as cursor:
        cursor.execute(ddl)
    conn.commit()
    log("Ensured schema_migrations table exists.")


def already_applied(conn, filename: str, checksum: str) -> bool:
    query = (
        "SELECT 1 FROM schema_migrations "
        "WHERE filename = %s AND checksum = %s AND success = 1 LIMIT 1"
    )
    with conn.cursor() as cursor:
        cursor.execute(query, (filename, checksum))
        return cursor.fetchone() is not None


def mark_applied(conn, filename: str, checksum: str) -> None:
    query = (
        "INSERT INTO schema_migrations (filename, checksum, success) "
        "VALUES (%s, %s, 1)"
    )
    with conn.cursor() as cursor:
        cursor.execute(query, (filename, checksum))
    conn.commit()


def is_idempotent_ddl_error(err: Error, statement: str) -> bool:
    stmt = statement.strip().upper()
    # Safe-to-ignore cases for repeatable migrations on partially applied DDL files.
    if err.errno in {1007, 1050, 1060, 1061}:  # db exists, table exists, dup column, dup key
        return True
    if err.errno == 1091 and ("DROP INDEX" in stmt or "DROP COLUMN" in stmt or "DROP FOREIGN KEY" in stmt):
        return True
    return False


def execute_sql_file(conn, path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    log(f"Applying file: {path.name}")

    stmt_idx = 0
    with conn.cursor() as cursor:
        for statement in sqlparse.split(sql_text):
            stmt = statement.strip()
            if not stmt:
                continue

            stmt_idx += 1
            compact_stmt = " ".join(stmt.split())
            if len(compact_stmt) > 140:
                compact_stmt = compact_stmt[:137] + "..."

            try:
                cursor.execute(stmt)
                if cursor.with_rows:
                    cursor.fetchall()
                log(f"  statement {stmt_idx}: ok | {compact_stmt}")
            except Error as err:
                if is_idempotent_ddl_error(err, stmt):
                    log(f"  statement {stmt_idx}: skip-idempotent ({err.errno}) | {compact_stmt}")
                    continue
                conn.rollback()
                raise

        conn.commit()

    log(f"Finished file: {path.name} (statements: {stmt_idx})")


def resolve_migration_files(migrations_dir: Path, explicit_files: List[str]) -> Iterable[Path]:
    if explicit_files:
        for name in explicit_files:
            p = migrations_dir / name
            if not p.exists():
                raise FileNotFoundError(f"Migration file not found: {p}")
            yield p
        return

    preferred = ["init.sql", "indexes.sql"]
    emitted = set()
    for name in preferred:
        p = migrations_dir / name
        if p.exists():
            emitted.add(p.name)
            yield p

    for p in sorted(migrations_dir.glob("*.sql")):
        if p.name not in emitted:
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MySQL schema migrations.")
    parser.add_argument("--migrations-dir", default="/migrations", help="Directory containing SQL migration files")
    parser.add_argument("--files", default="", help="Comma-separated migration files in execution order")
    args = parser.parse_args()

    host = env("MYSQL_HOST", "mysql")
    port = int(env("MYSQL_PORT", "3306"))
    database = env("MYSQL_DATABASE", "InfoSearch")
    user = env("MYSQL_USER", "user")
    password = env("MYSQL_PASSWORD", "pass")
    allow_create = to_bool(os.getenv("MYSQL_CREATE_DATABASE", "true"))

    migrations_dir = Path(args.migrations_dir)
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory does not exist: {migrations_dir}")

    explicit_files = [f.strip() for f in args.files.split(",") if f.strip()]

    log("Starting migration run.")
    log(f"Target: {user}@{host}:{port}/{database}")
    log(f"Migrations directory: {migrations_dir}")

    ensure_database(host, port, user, password, database, allow_create)

    conn = connect_with_retry(
        {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "autocommit": False,
        }
    )

    try:
        ensure_schema_migrations_table(conn)

        files = list(resolve_migration_files(migrations_dir, explicit_files))
        if not files:
            log("No migration files found. Nothing to do.")
            return 0

        for path in files:
            checksum = checksum_file(path)
            if already_applied(conn, path.name, checksum):
                log(f"Skipping already applied file: {path.name}")
                continue

            execute_sql_file(conn, path)
            mark_applied(conn, path.name, checksum)
            log(f"Recorded migration: {path.name}")

        log("All migrations applied successfully.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"Migration failed: {exc}")
        sys.exit(1)
