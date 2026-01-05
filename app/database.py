from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import enum
import uuid

from config import settings

# --- Modello del Database ---

Base = declarative_base()

class MessageStatus(str, enum.Enum):
    """Stato di un messaggio spotted."""
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"
    REVIEW = "review"
    FAILED = "failed"

class UserStatus(str, enum.Enum):
    """Stato di un utente tecnico."""
    ACTIVE = "active"
    LIMITED = "limited"
    BLOCKED = "blocked"

class TechnicalUser(Base):
    """Modello per un utente tecnico anonimo."""
    __tablename__ = "technical_users"

    id = Column(String, primary_key=True, index=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trust_score = Column(Integer, default=100)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

    messages = relationship("SpottedMessage", back_populates="author")

class SpottedMessage(Base):
    """Modello per un messaggio spotted nel database."""
    __tablename__ = "spotted_messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    media_pk = Column(String, nullable=True)
    admin_note = Column(String, nullable=True)
    gemini_analysis = Column(String, nullable=True)
    
    technical_user_id = Column(String, ForeignKey("technical_users.id"))
    author = relationship("TechnicalUser", back_populates="messages")

# --- Configurazione del Database ---

if settings.database.db_url.startswith("sqlite"):
    engine = create_engine(
        settings.database.db_url,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.database.db_url)

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

# --- NUOVE FUNZIONI CRUD PER TECHNICAL USER ---

def get_technical_user(db: Session, technical_user_id: str) -> TechnicalUser | None:
    """Recupera un utente tecnico dal suo ID."""
    return db.query(TechnicalUser).filter(TechnicalUser.id == technical_user_id).first()

def create_technical_user(db: Session) -> TechnicalUser:
    """Crea un nuovo utente tecnico con un UUID."""
    new_user = TechnicalUser(id=str(uuid.uuid4()))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_or_create_technical_user(db: Session, technical_user_id: str | None) -> tuple[TechnicalUser, bool]:
    """
    Recupera un utente tecnico se l'ID è valido, altrimenti ne crea uno nuovo.
    Restituisce l'utente e un booleano che indica se è stato creato.
    """
    created = False
    user = None
    if technical_user_id:
        user = get_technical_user(db, technical_user_id)
    
    if user:
        # Utente trovato, aggiorna last_seen_at
        user.last_seen_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    else:
        # Utente non trovato o ID non fornito, creane uno nuovo
        user = create_technical_user(db)
        created = True
        
    return user, created