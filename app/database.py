from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

from config import settings

# --- Modello del Database ---

Base = declarative_base()

class MessageStatus(str, enum.Enum):
    """Stato di un messaggio spotted."""
    PENDING = "pending"    # In attesa di revisione manuale
    APPROVED = "approved"  # Approvato e pronto per la pubblicazione
    POSTED = "posted"      # Pubblicato con successo
    REJECTED = "rejected"    # Rifiutato (dall'AI o manualmente)
    REVIEW = "review"      # Necessita di revisione manuale (suggerito da AI)
    FAILED = "failed"      # Processo di pubblicazione fallito

class SpottedMessage(Base):
    """Modello per un messaggio spotted nel database."""
    __tablename__ = "spotted_messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True) # Per loggare errori o info dall'AI
    media_pk = Column(String, nullable=True) # ID del media postato su Instagram
    admin_note = Column(String, nullable=True)
    gemini_analysis = Column(String, nullable=True) # New field for Gemini's moderation analysis # Nota privata per admin

# --- Configurazione del Database ---

# Logica per creare il motore del database
if settings.database.db_url.startswith("sqlite"):
    # Configurazione specifica per SQLite
    engine = create_engine(
        settings.database.db_url,
        connect_args={"check_same_thread": False}
    )
else:
    # Configurazione per altri database (es. PostgreSQL)
    engine = create_engine(settings.database.db_url)

# Crea una sessione del database configurata
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Funzioni di Utilità ---

def get_db():
    """Funzione di dipendenza per ottenere una sessione del database per ogni richiesta."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """Crea le tabelle del database se non esistono già."""
    Base.metadata.create_all(bind=engine)
