#!/usr/bin/env python3
"""One-liner test: rebuild info cards and verify."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType, get_or_create_technical_user
from datetime import datetime

db = SessionLocal()

# Delete old
deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
db.commit()
print(f"✅ Deleted {deleted} old INFO cards")

# Create new
technical_user, _ = get_or_create_technical_user(db, None)
cards_data = [
    {"title": "🌟 Benvenuto", "text": "Ciao! Condividi gossip e curiosità in anonimo"},
    {"title": "📋 Regole", "text": "Rispetta gli altri. Niente offese o insulti"},
    {"title": "🔐 Privacy", "text": "I dati sono protetti. Nessuna vendita di info"},
    {"title": "💬 Come Funziona", "text": "Invia dal form anonimo. Approvato = pubblicato"},
    {"title": "⭐ Daily Recap", "text": "Ogni giorno ore 20:00 carousel dei migliori spotted"}
]

created = []
for d in cards_data:
    card = SpottedMessage(
        title=d["title"],
        text=d["text"],
        message_type=MessageType.INFO,
        status=MessageStatus.APPROVED,
        technical_user_id=technical_user.id,
        created_at=datetime.utcnow()
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    created.append(card.id)
    print(f"✅ Created ID {card.id}: {card.title}")

print(f"\n✅ Total: {len(created)} new INFO cards created with v5 style template")

# Test daily post
print(f"\n🧪 Testing daily_post_task...")
from app.tasks import daily_post_task
result = daily_post_task()
print(f"Result: {result.get('status')} - {result.get('message')}")

db.close()
print("\n✅ DONE")
