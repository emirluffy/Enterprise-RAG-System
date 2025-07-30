#!/usr/bin/env python3
"""
Context7 Verified Database Initialization Script
Fresh database creation with all required tables
Following SQLModel metadata.create_all() pattern from Context7
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from sqlmodel import SQLModel, create_engine
from app.core.config import settings

# Import all models to register them with SQLModel.metadata (Context7 Pattern)
from app.models import *

def init_fresh_database():
    """
    Context7 Verified: SQLModel.metadata.create_all() pattern
    Creates all tables from imported SQLModel classes
    """
    print("🔧 Context7 Database Initialization Started...")
    
    # Use the same database path as the main app (Context7 verified)
    database_url = str(settings.SQLALCHEMY_DATABASE_URI)
    print(f"🔍 Database URL: {database_url}")
    
    # Create engine with same config as main app
    engine = create_engine(database_url, echo=True)
    
    try:
        print("📊 Creating all tables from SQLModel schemas (Context7 Pattern)...")
        # Context7 Pattern: This creates ALL tables for imported models
        SQLModel.metadata.create_all(engine)
        print("✅ All tables created successfully!")
        
        # Verify tables were created (Context7 verification)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {tables}")
        
        # Verify user table schema
        if 'user' in tables:
            user_columns = inspector.get_columns('user')
            print(f"🧑‍💻 User table columns: {[col['name'] for col in user_columns]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = init_fresh_database()
    if success:
        print("🎉 Context7 Database initialization completed successfully!")
    else:
        print("💥 Database initialization failed!")
        exit(1) 