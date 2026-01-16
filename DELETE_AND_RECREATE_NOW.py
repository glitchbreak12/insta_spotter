#!/usr/bin/env python3
"""FORCE DELETE and RECREATE info cards NOW - Direct DB operations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

from sqlalchemy import text
from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType, get_or_create_technical_user
from datetime import datetime

db = SessionLocal()

try:
    # STEP 1: FORCE DELETE using raw SQL to ensure it works
    print("🔴 CANCELLAZIONE TOTALE INFO CARD DAL DATABASE")
    print("-" * 60)
    
    # Get all INFO cards first
    all_info = db.query(SpottedMessage).filter(
        SpottedMessage.message_type == MessageType.INFO
    ).all()
    
    print(f"Trovate {len(all_info)} info card nel DB:")
    for card in all_info:
        print(f"  - ID {card.id}: {card.title}")
    
    # Delete them
    if all_info:
        for card in all_info:
            db.delete(card)
        db.commit()
        print(f"\n✅ CANCELLATE {len(all_info)} info card\n")
    else:
        print("✅ Nessuna info card trovata (già cancellate?)\n")
    
    # STEP 2: CREATE 5 NEW INFO CARDS
    print("🟢 CREAZIONE 5 NUOVE INFO CARD")
    print("-" * 60)
    
    technical_user, _ = get_or_create_technical_user(db, None)
    
    new_cards_data = [
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
    
    created_cards = []
    for i, data in enumerate(new_cards_data, 1):
        card = SpottedMessage(
            title=data["title"],
            text=data["text"],
            message_type=MessageType.INFO,
            status=MessageStatus.APPROVED,
            technical_user_id=technical_user.id,
            created_at=datetime.utcnow()
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        created_cards.append(card)
        print(f"{i}. ✅ Created ID {card.id}: {card.title}")
    
    # STEP 3: VERIFY in DB
    print(f"\n📊 VERIFICA DATABASE")
    print("-" * 60)
    final_count = db.query(SpottedMessage).filter(
        SpottedMessage.message_type == MessageType.INFO
    ).count()
    print(f"✅ Info card nel database adesso: {final_count}")
    
    # STEP 4: List all
    print(f"\n📝 LISTA FINALE:")
    final_cards = db.query(SpottedMessage).filter(
        SpottedMessage.message_type == MessageType.INFO
    ).order_by(SpottedMessage.id).all()
    
    for card in final_cards:
        print(f"  ID {card.id}: {card.title}")
    
    print("\n" + "=" * 60)
    print("✅ DONE! Info cards ricreate da zero nel database")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
