#!/usr/bin/env python3
"""
Script to create the activity_logs table in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.activity_log import ActivityLog

def create_activity_log_table():
    """Create the activity_logs table"""
    try:
        ActivityLog.__table__.create(engine, checkfirst=True)
        print("✅ Activity logs table created successfully")
    except Exception as e:
        print(f"❌ Error creating activity logs table: {e}")

if __name__ == "__main__":
    create_activity_log_table()