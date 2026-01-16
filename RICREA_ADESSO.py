#!/usr/bin/env python3
"""IMMEDIATE ACTION: Delete ALL info cards and recreate from zero."""

import os
import sys

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

# Import after path setup
from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType, get_or_create_technical_user
from datetime import datetime

print("\n" + "🔴 " * 40)
print("CANCELLAZIONE TOTALE E RICREAZIONE DA ZERO")
print("🔴 " * 40)

db = SessionLocal()

try:
    # STEP 1: Delete EVERYTHING
    print("\n1️⃣ CANCELLAZIONE TOTALE di tutte le INFO card...")
    all_info = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).all()
    print(f"   Found {len(all_info)} info card nel database")
    
    for card in all_info:
        print(f"      - Deleting ID {card.id}: {card.title}")
    
    deleted_count = db.query(SpottedMessage).filter(
        SpottedMessage.message_type == MessageType.INFO
    ).delete(synchronize_session=False)
    db.commit()
    print(f"   ✅ CANCELLATE {deleted_count} info card dal database\n")
    
    # Verify deletion
    verify_deleted = db.query(SpottedMessage).filter(MessageType.INFO == MessageType.INFO).count()
    print(f"   Verifica: {verify_deleted} info card rimaste (dovrebbe essere 0)")
    
    # STEP 2: Create NEW ones from scratch
    print("\n2️⃣ CREAZIONE DI 5 NUOVE INFO CARD COMPLETAMENTE NUOVE...")
    
    technical_user, created_user = get_or_create_technical_user(db, None)
    print(f"   Using technical user: {technical_user.id} (created={created_user})")
    
    # NEW info cards with fresh content
    new_cards = [
        {
            "title": "🌟 Benvenuto in Spotted",
            "text": "Ciao! Sei nel posto giusto per condividere momenti speciali, curiosità e gossip della tua comunità in perfetto anonimato. Unisciti a migliaia di utenti che già si divertono qui!"
        },
        {
            "title": "📋 Regole della Community",
            "text": "1. Rispetta gli altri sempre\n2. NO insulti o offese\n3. NO contenuti illegali\n4. Sii divertente e costruttivo\n\nViolando queste regole il tuo messaggio sarà rimosso."
        },
        {
            "title": "🔐 Privacy & GDPR",
            "text": "La tua privacy è la nostra priorità:\n✓ Invii completamente anonimi\n✓ Dati protetti e crittografati\n✓ Conformità GDPR totale\n✓ Zero tracking o vendita dati"
        },
        {
            "title": "💬 Come Funziona",
            "text": "È semplicissimo:\n1. Scrivi il tuo spotted\n2. Invia dal form anonimo\n3. Aspetta l'approvazione\n4. Apparirà nella feed pubblica\n\nTutto in perfetto anonimato!"
        },
        {
            "title": "⭐ Spotted del Giorno",
            "text": "Ogni sera alle 20:00 pubblichiamo il Daily Recap: un carousel con i 20 migliori spotted della giornata. Non perdere il tuo momento di gloria! 🚀"
        }
    ]
    
    created_ids = []
    for i, card_data in enumerate(new_cards, 1):
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
        created_ids.append(card.id)
        print(f"   {i}. ✅ Created ID {card.id:3d} | {card.title}")
    
    # STEP 3: Verify they exist
    print(f"\n3️⃣ VERIFICA CREAZIONE...")
    info_count = db.query(SpottedMessage).filter(MessageType.INFO == MessageType.INFO).count()
    print(f"   ✅ {info_count} info card adesso nel database (dovrebbe essere 5)")
    
    # STEP 4: Test image generation for each
    print(f"\n4️⃣ TEST GENERAZIONE IMMAGINI (v5 style)...")
    from app.image.generator import ImageGenerator
    import time
    
    generator = ImageGenerator()
    for card_id in created_ids:
        card = db.query(SpottedMessage).filter(SpottedMessage.id == card_id).first()
        if not card:
            continue
        
        try:
            image_path = generator.from_text(
                card.text,
                f"info_card_{card_id}_{int(time.time())}.png",
                card_id,
                message_type="info",
                title=card.title
            )
            
            if image_path:
                print(f"   ✅ ID {card_id}: generata immagine v5 style")
            else:
                print(f"   ⚠️  ID {card_id}: fallita generazione")
        except Exception as e:
            print(f"   ⚠️  ID {card_id}: errore - {str(e)[:50]}")
    
    # STEP 5: Test daily post
    print(f"\n5️⃣ TEST DAILY POST TASK...")
    from app.tasks import daily_post_task
    
    result = daily_post_task()
    print(f"   Status: {result.get('status')}")
    print(f"   Message: {result.get('message')}")
    
    if result.get('status') in ('success', 'simulated', 'already_run', 'no_messages'):
        print(f"   ✅ Daily post task working!")
    else:
        print(f"   ⚠️  Daily post task issue")
    
    print("\n" + "🟢 " * 40)
    print("✅ RICREAZIONE COMPLETATA CON SUCCESSO")
    print("🟢 " * 40 + "\n")

except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
