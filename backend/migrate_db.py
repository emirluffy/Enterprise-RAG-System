#!/usr/bin/env python3
"""
Temporary script to add missing columns to User table
This fixes the 'no such column: user.bio' error
"""
import sqlite3
import os

# Database path (multiple possible locations)
possible_paths = [
    os.path.join(os.path.dirname(__file__), "app.db"),
    os.path.join(os.path.dirname(__file__), "app", "app.db"),
    "app.db"
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ Database file not found in any of the expected locations:")
    for path in possible_paths:
        print(f"   - {path}")
    exit(1)

print(f"🔍 Found database at: {db_path}")

def migrate_user_table():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current columns
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns one by one
        columns_to_add = [
            ("bio", "TEXT"),
            ("workspace_id", "TEXT"),
            ("total_documents_uploaded", "INTEGER DEFAULT 0"),
            ("total_conversations", "INTEGER DEFAULT 0"),
            ("favorite_topics", "TEXT"),  # JSON as TEXT in SQLite
            ("recent_searches", "TEXT"),   # JSON as TEXT in SQLite
            ("updated_at", "DATETIME")
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⏭️ Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding {column_name}: {e}")
            else:
                print(f"⏭️ Column {column_name} already exists")
        
        # Update preferences column to have proper default
        try:
            cursor.execute("""
                UPDATE user 
                SET preferences = '{"theme":"twilight-dream","language":"tr","sidebar_collapsed":false,"default_ai_model":"gemini-2.5-flash-lite","response_style":"detailed","enable_ai_enhancement":true,"workspace_name":"Kişisel Çalışma Alanı","auto_save_conversations":true,"enable_notifications":true,"email_notifications":false,"document_upload_notifications":true}'
                WHERE preferences IS NULL OR preferences = '{}'
            """)
            print("✅ Updated default preferences")
        except Exception as e:
            print(f"⚠️ Error updating preferences: {e}")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Starting User table migration...")
    migrate_user_table() 