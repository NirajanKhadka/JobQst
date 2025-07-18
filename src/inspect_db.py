#!/usr/bin/env python3
"""
Quick database inspection script
"""

import sqlite3
import os

db_path = "data/jobs.db"

if not os.path.exists(db_path):
    print(f"❌ Database {db_path} does not exist")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📊 Database: {db_path}")
    print(f"📋 Tables found: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        print(f"\n🗂️ Table: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("   Columns:")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"   📊 Rows: {count}")
        
        # Show sample data if exists
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            sample_rows = cursor.fetchall()
            print(f"   📄 Sample data:")
            for i, row in enumerate(sample_rows, 1):
                print(f"     Row {i}: {str(row)[:100]}...")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
