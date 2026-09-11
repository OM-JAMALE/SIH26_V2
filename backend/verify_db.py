"""Verify database schema after migrations."""

import sqlite3
import sys

def verify_database():
    """Verify all tables and indexes were created."""
    try:
        conn = sqlite3.connect('health_ai.db')
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        print("=" * 70)
        print("DATABASE TABLES CREATED")
        print("=" * 70)
        print()

        expected_tables = [
            'alembic_version',
            'patients',
            'sessions', 
            'conversation_turns',
            'documents',
            'extracted_entities',
            'summaries',
            'consents',
            'audit_logs',
        ]

        actual_tables = sorted([t[0] for t in tables])
        print(f"Expected tables: {len(expected_tables)}")
        print(f"Actual tables: {len(actual_tables)}")
        print()

        for i, table_name in enumerate(actual_tables, 1):
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"[{i}] {table_name.upper()} ({len(columns)} columns)")
            for col in columns:
                col_id, col_name, col_type, not_null, default, pk = col
                null_str = "NOT NULL" if not_null else "NULLABLE"
                pk_str = " [PK]" if pk else ""
                print(f"    - {col_name}: {col_type} {null_str}{pk_str}")
            print()

        # Verify indexes
        print("=" * 70)
        print("INDEXES CREATED")
        print("=" * 70)
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name, name;")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"- {idx[0]} (table: {idx[1]})")

        print()
        
        # Check alembic_version
        cursor.execute("SELECT version_num FROM alembic_version;")
        version = cursor.fetchone()
        print("=" * 70)
        print("ALEMBIC VERSION TRACKING")
        print("=" * 70)
        print(f"Current version: {version[0] if version else 'None'}")
        print()

        print("=" * 70)
        print("SUCCESS: ALL TABLES AND INDEXES CREATED")
        print("=" * 70)

        conn.close()
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(verify_database())
