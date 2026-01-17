#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.getcwd())

# Test the style config system
from app.database import create_db_and_tables, create_default_info_card_styles, SessionLocal
from app.database import get_style_configs

print('Testing database connection...')
create_db_and_tables()

print('Creating default styles...')
db = SessionLocal()
try:
    create_default_info_card_styles(db)
    styles = get_style_configs(db, 'info_card')
    print(f'Found {len(styles)} styles:')
    for style in styles:
        print(f'  - {style.name} (ID: {style.id})')
        print(f'    Config length: {len(style.config) if style.config else 0}')
        print(f'    Default: {style.is_default}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()

print('Database test completed.')
