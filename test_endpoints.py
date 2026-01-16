#!/usr/bin/env python3
"""Test the new endpoints and verify that changes actually work."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType
from datetime import datetime

print("=== TESTING ENDPOINTS ===\n")

db = SessionLocal()

# Test 1: Check if there are any messages
print("1. Checking if messages exist...")
messages = db.query(SpottedMessage).all()
print(f"   Total messages in DB: {len(messages)}")
for status in MessageStatus:
    count = db.query(SpottedMessage).filter(SpottedMessage.status == status).count()
    print(f"   - {status.value}: {count}")

# Test 2: Check if there are any INFO cards
print("\n2. Checking INFO cards (info-cards)...")
info_cards = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).all()
print(f"   Total INFO cards: {len(info_cards)}")
if info_cards:
    for card in info_cards[:3]:
        print(f"     - ID {card.id}: {card.title}")

# Test 3: Create a test message for testing publish-now
print("\n3. Creating a test message for publish-now endpoint...")
test_msg = SpottedMessage(
    text="Test message for publish-now endpoint",
    message_type=MessageType.SPOTTED,
    status=MessageStatus.APPROVED,
    created_at=datetime.utcnow()
)
db.add(test_msg)
db.commit()
db.refresh(test_msg)
test_msg_id = test_msg.id
print(f"   Created test message ID: {test_msg_id}")

# Test 4: Manually test the post_single_message function
print(f"\n4. Testing post_single_message function directly...")
from app.admin.routes import post_single_message
try:
    print(f"   Calling post_single_message({test_msg_id})...")
    result = post_single_message(test_msg_id)
    print(f"   Result: {result}")
    
    # Verify the message status changed
    db.refresh(test_msg)
    print(f"   Message status after: {test_msg.status.value}")
    print(f"   Message media_pk: {test_msg.media_pk}")
    print(f"   Message error_message: {test_msg.error_message}")
    
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check daily post settings
print("\n5. Checking daily post settings...")
from app.database import get_daily_post_settings
try:
    settings = get_daily_post_settings(db)
    if settings:
        print(f"   Settings exist: ID={settings.id}, enabled={settings.enabled}")
    else:
        print(f"   No settings found (will be created on next daily_post_task)")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 6: Test the recreate info cards logic directly
print("\n6. Testing recreate info cards logic...")
try:
    from app.database import get_or_create_technical_user
    
    # Delete all existing info cards
    deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
    db.commit()
    print(f"   Deleted {deleted} existing INFO cards")
    
    # Create defaults
    technical_user, created = get_or_create_technical_user(db, None)
    print(f"   Technical user: ID={technical_user.id}, created={created}")
    
    defaults = [
        {"title": "Aggiornamento Importante", "text": "Abbiamo rilasciato una nuova versione!"},
        {"title": "Regole della Community", "text": "Rispetta gli altri utenti."},
        {"title": "GPDR & Privacy", "text": "I dati sono trattati in conformità."},
        {"title": "Come funziona", "text": "Invia il tuo spotted in forma anonima."}
    ]
    
    created_ids = []
    for d in defaults:
        card = SpottedMessage(
            title=d['title'],
            text=d['text'],
            message_type=MessageType.INFO,
            status=MessageStatus.APPROVED,
            technical_user_id=technical_user.id
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        created_ids.append(card.id)
        print(f"   Created INFO card ID: {card.id}")
    
    print(f"   Total created: {len(created_ids)}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()

# Verify
print("\n7. Verifying changes...")
info_cards_after = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).all()
print(f"   INFO cards after recreation: {len(info_cards_after)}")
for card in info_cards_after:
    print(f"     - ID {card.id}: {card.title}")

print("\n=== TEST COMPLETE ===")
db.close()
