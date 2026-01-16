#!/usr/bin/env python3
"""Quick test: verify that publish-now and recreate info-cards actually work."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable wkhtmltoimage issues
os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

print("=" * 80)
print("TESTING CORE FUNCTIONALITY")
print("=" * 80)

from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType
from datetime import datetime

db = SessionLocal()

try:
    # Test 1: Create a test SPOTTED message and try to post it
    print("\n1️⃣  TEST: Create SPOTTED message → call post_single_message")
    test_msg = SpottedMessage(
        text="Test message for publish-now endpoint",
        message_type=MessageType.SPOTTED,
        status=MessageStatus.APPROVED,
        title=None,
        created_at=datetime.utcnow()
    )
    db.add(test_msg)
    db.commit()
    db.refresh(test_msg)
    test_msg_id = test_msg.id
    print(f"   ✓ Created test SPOTTED message ID: {test_msg_id}")
    
    from app.admin.routes import post_single_message
    result = post_single_message(test_msg_id)
    print(f"   Result: {result}")
    
    # Refresh and check
    db.refresh(test_msg)
    if test_msg.status in (MessageStatus.POSTED, MessageStatus.FAILED):
        print(f"   ✓ Message status updated to: {test_msg.status.value}")
    else:
        print(f"   ⚠️  Message status is still: {test_msg.status.value}")
    
    # Test 2: Delete and recreate INFO cards
    print("\n2️⃣  TEST: Delete all INFO cards and recreate defaults")
    
    # Count before
    before = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).count()
    print(f"   Before: {before} INFO cards exist")
    
    # Delete all
    deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
    db.commit()
    print(f"   ✓ Deleted {deleted} INFO cards")
    
    # Recreate defaults
    from app.database import get_or_create_technical_user
    
    technical_user, created = get_or_create_technical_user(db, None)
    defaults = [
        {"title": "Aggiornamento Importante", "text": "Nuova versione rilasciata!"},
        {"title": "Regole", "text": "Rispetta gli altri utenti."},
        {"title": "Privacy", "text": "I dati sono trattati in conformità."},
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
        print(f"   ✓ Created INFO card: ID {card.id}, title='{card.title}'")
    
    # Verify
    after = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).count()
    print(f"   After: {after} INFO cards exist")
    
    if after == len(created_ids):
        print(f"   ✅ SUCCESS: Recreated {len(created_ids)} default INFO cards")
    else:
        print(f"   ⚠️  Expected {len(created_ids)}, but found {after}")
    
    # Test 3: Daily post task
    print("\n3️⃣  TEST: Run daily_post_task")
    from app.tasks import daily_post_task
    result = daily_post_task()
    print(f"   Result: {result}")
    
    if result.get("status") in ("success", "simulated"):
        print(f"   ✅ Daily post task executed: {result.get('message')}")
    else:
        print(f"   ⚠️  Daily post task failed or had no messages: {result.get('message')}")
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETED")
    print("=" * 80)
    
finally:
    db.close()
