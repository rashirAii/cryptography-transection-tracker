"""
Cryptocurrency Transaction Tracker - SQL Execution & Analytics Script
Automates SQLite database setup, schema migration, seed loading, triggers, and query verification.
"""

import os
import sqlite3
import sys

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_FILE = "crypto_tracker.db"
SCHEMA_FILE = "schema.sql"
SEED_FILE = "seed.sql"
VIEWS_TRIGGERS_FILE = "views_and_triggers.sql"
ANALYTICS_FILE = "analytics_queries.sql"

def print_separator(title):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)

def format_table(headers, rows):
    if not rows:
        return "No data returned."
    
    # Calculate max column widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val if val is not None else 'NULL')))
    
    # Build format string
    header_str = " | ".join(f"{str(h):<{widths[i]}}" for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * widths[i] for i in range(len(headers)))
    
    lines = [header_str, sep_str]
    for row in rows:
        row_str = " | ".join(f"{str(val if val is not None else 'NULL'):<{widths[i]}}" for i, val in enumerate(row))
        lines.append(row_str)
    
    return "\n".join(lines)

def run_script(cursor, filepath):
    if not os.path.exists(filepath):
        print(f"[ERROR] File {filepath} not found.")
        sys.exit(1)
    
    with open(filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    try:
        cursor.executescript(sql_content)
        print(f"[OK] Successfully executed: {filepath}")
    except Exception as e:
        print(f"[ERROR] Error executing {filepath}: {e}")
        sys.exit(1)

def run_analytics(cursor, filepath):
    if not os.path.exists(filepath):
        print(f"[ERROR] File {filepath} not found.")
        sys.exit(1)
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_queries = content.split("-- --------------------------------------------------------------------")
    
    query_num = 1
    for raw_q in raw_queries:
        sql = raw_q.strip()
        if not sql:
            continue
        
        lines = [line.strip() for line in sql.splitlines() if line.strip()]
        title_line = [l for l in lines if l.startswith("-- QUERY")]
        
        query_title = title_line[0].replace("--", "").strip() if title_line else f"Analytics Query #{query_num}"
        
        clean_sql = "\n".join([line for line in sql.splitlines() if not line.strip().startswith("--")])
        
        if clean_sql.strip():
            print_separator(query_title)
            try:
                cursor.execute(clean_sql)
                headers = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                print(format_table(headers, rows))
                print(f"\n[INFO] Total Rows: {len(rows)}")
                query_num += 1
            except Exception as e:
                print(f"[ERROR] Execution Error on {query_title}: {e}")

def main():
    print_separator("Initializing Cryptocurrency Transaction Tracker Project")
    
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"[INFO] Cleaned up previous database file: {DB_FILE}")
        except Exception:
            pass
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    print("\n--- 1. Creating Database Schema ---")
    run_script(cursor, SCHEMA_FILE)
    
    print("\n--- 2. Setting Up Views & Triggers ---")
    run_script(cursor, VIEWS_TRIGGERS_FILE)
    
    print("\n--- 3. Populating Seed Data ---")
    run_script(cursor, SEED_FILE)
    
    print("\n--- 4. Running Analytical Business Queries ---")
    run_analytics(cursor, ANALYTICS_FILE)
    
    conn.commit()
    conn.close()
    
    print_separator("Execution Completed Successfully")
    print(f"[INFO] Database created: {os.path.abspath(DB_FILE)}")
    print("[INFO] You can inspect the database or run custom queries using SQLite CLI or DBeaver / TablePlus.")

if __name__ == "__main__":
    main()
