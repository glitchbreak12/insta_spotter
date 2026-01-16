$script = @'
import os, sys
sys.path.insert(0, "C:\Users\gmape\Desktop\projects\insta_spotter")
os.environ["DISABLE_WKHTMLTOIMAGE"] = "1"

from app.database import SessionLocal, SpottedMessage, MessageStatus, MessageType, get_or_create_technical_user
from datetime import datetime

db = SessionLocal()

print("\n" + "=" * 60)
print("CANCELLA TUTTE LE INFO CARD VECCHIE")
print("=" * 60)

# DELETE ALL
all_info = db.query(SpottedMessage).filter(SpottedMessage.message_type == MessageType.INFO).all()
print(f"\nTrovate {len(all_info)} info card da cancellare")
for card in all_info:
    print(f"  - ID {card.id}: {card.title}")
    db.delete(card)
db.commit()
print(f"✅ CANCELLATE {len(all_info)}")

print("\n" + "=" * 60)
print("RICREA 5 NUOVE INFO CARD")
print("=" * 60)

technical_user, _ = get_or_create_technical_user(db, None)

cards = [
    {"title": "🌟 Benvenuto", "text": "Ciao! Condividi momenti speciali in anonimato"},
    {"title": "📋 Regole", "text": "Rispetta gli altri. No insulti o contenuti illegali"},
    {"title": "🔐 Privacy", "text": "Dati protetti, GDPR compliant, zero vendite"},
    {"title": "💬 Come", "text": "Scrivi → invia anonimo → aspetta approvazione → pubblicato"},
    {"title": "⭐ Daily", "text": "Ore 20:00 carousel con i 20 best spotted della giornata"}
]

for i, d in enumerate(cards, 1):
    card = SpottedMessage(title=d["title"], text=d["text"], message_type=MessageType.INFO, status=MessageStatus.APPROVED, technical_user_id=technical_user.id, created_at=datetime.utcnow())
    db.add(card)
    db.commit()
    db.refresh(card)
    print(f"{i}. ✅ ID {card.id}: {card.title}")

print("\n✅ RICREAZIONE COMPLETATA")
print("=" * 60)
db.close()
'@

python -c $script
