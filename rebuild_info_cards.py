#!/usr/bin/env python3
"""Clean rebuild: delete ALL old info cards and recreate with new v5 style."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType, get_or_create_technical_user
from datetime import datetime

print("\n" + "=" * 80)
print("🔄 CLEAN REBUILD: Delete old INFO cards and recreate with v5 style")
print("=" * 80)

db = SessionLocal()

try:
    # Step 1: DELETE ALL existing INFO cards
    print("\n1️⃣  Deleting all existing INFO cards...")
    old_count = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).count()
    print(f"   Found {old_count} old INFO cards")
    
    deleted = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).delete(synchronize_session=False)
    db.commit()
    print(f"   ✅ Deleted {deleted} INFO cards\n")
    
    # Step 2: CREATE NEW INFO cards with v5 style
    print("2️⃣  Creating new INFO cards with v5 style...")
    
    technical_user, _ = get_or_create_technical_user(db, None)
    
    new_info_cards = [
        {
            "title": "🌟 Benvenuto su Spotted",
            "text": "Ciao! Questo è il posto dove condividere gossip, curiosità e momenti speciali della tua comunità in forma anonima. Unisciti a noi!"
        },
        {
            "title": "📋 Regole della Community",
            "text": "Rispetta gli altri, senza offese o insulti. I messaggi scurrili o violenti verranno rimossi. Divertiti in modo responsabile!"
        },
        {
            "title": "🔐 Privacy e GDPR",
            "text": "I tuoi dati sono al sicuro. Trattiamo ogni informazione in conformità con le leggi sulla privacy. Nessun dato sarà venduto."
        },
        {
            "title": "💬 Come Funziona",
            "text": "Invia il tuo spotted dal form pubblico in forma anonima. Una volta approvato, apparirà nella nostra feed. Semplice e anonimo!"
        },
        {
            "title": "⭐ Spotted del Giorno",
            "text": "Ogni giorno pubblichiamo una compilation con i migliori spotted della giornata. Non perderti il daily recap alle 20:00!"
        }
    ]
    
    created_cards = []
    for card_data in new_info_cards:
        card = SpottedMessage(
            title=card_data["title"],
            text=card_data["text"],
            message_type=MessageType.INFO,
            status=MessageStatus.APPROVED,
            technical_user_id=technical_user.id,
            created_at=datetime.utcnow()
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        created_cards.append(card)
        print(f"   ✅ Created: ID {card.id:3d} | {card.title}")
    
    # Step 3: Test generating images for these new cards
    print(f"\n3️⃣  Testing image generation for new INFO cards...")
    from app.image.generator import ImageGenerator
    import time
    
    generator = ImageGenerator()
    generated_count = 0
    
    for card in created_cards[:1]:  # Test with first card only
        try:
            image_path = generator.from_text(
                card.text,
                f"info_card_test_{card.id}_{int(time.time())}.png",
                card.id,
                message_type="info",
                title=card.title
            )
            
            if image_path:
                print(f"   ✅ Generated image for ID {card.id}: {image_path}")
                generated_count += 1
            else:
                print(f"   ⚠️  Failed to generate image for ID {card.id}")
        except Exception as e:
            print(f"   ⚠️  Error generating image for ID {card.id}: {e}")
    
    # Step 4: Test daily post task
    print(f"\n4️⃣  Testing daily_post_task...")
    from app.tasks import daily_post_task
    
    result = daily_post_task()
    print(f"   Result: {result}")
    
    if result.get("status") in ("success", "simulated", "no_messages", "already_run"):
        print(f"   ✅ Daily post task executed successfully\n")
    else:
        print(f"   ⚠️  Daily post task returned error\n")
    
    # Final verification
    print("5️⃣  Final Verification")
    info_count_final = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).count()
    print(f"   ✅ Total INFO cards in DB: {info_count_final}")
    print(f"   ✅ Images generated: {generated_count}")
    
    print("\n" + "=" * 80)
    print("✅ REBUILD COMPLETE")
    print("=" * 80 + "\n")
    
finally:
    db.close()
