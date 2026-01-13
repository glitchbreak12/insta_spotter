from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
from datetime import datetime
import enum
import uuid
from typing import Optional, Tuple

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

class MessageType(str, enum.Enum):
    """Tipo di messaggio."""
    SPOTTED = "spotted"  # Messaggio normale inviato dagli utenti
    INFO = "info"       # Card informativa creata dall'admin

class UserStatus(str, enum.Enum):
    """Stato di un utente tecnico."""
    ACTIVE = "active"
    LIMITED = "limited"
    BLOCKED = "blocked"

class DailyPostStyle(str, enum.Enum):
    """Stili disponibili per il post giornaliero."""
    GRID = "grid"  # Griglia di miniature
    CAROUSEL = "carousel"  # Carousel Instagram
    COMPACT = "compact"  # Layout compatto
    ELEGANT = "elegant"  # Stile elegante

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
    message_type = Column(Enum(MessageType), default=MessageType.SPOTTED, nullable=False)
    title = Column(String, nullable=True)  # Titolo personalizzato per info cards
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    media_pk = Column(String, nullable=True)
    admin_note = Column(String, nullable=True)
    gemini_analysis = Column(String, nullable=True)
    
    technical_user_id = Column(String, ForeignKey("technical_users.id"))
    author = relationship("TechnicalUser", back_populates="messages")

class AIModel(str, enum.Enum):
    """Modelli AI disponibili per la moderazione."""
    GEMINI = "gemini"
    GROK = "grok"
    LOCAL = "local"
    DISABLED = "disabled"

class AIConfig(Base):
    """Configurazione per l'AI e moderazione."""
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Integer, default=1)  # 1=abilitato, 0=disabilitato
    selected_model = Column(Enum(AIModel), default=AIModel.GEMINI, nullable=False)
    gemini_api_key = Column(String, nullable=True)
    grok_api_key = Column(String, nullable=True)
    local_model_path = Column(String, nullable=True)
    moderation_enabled = Column(Integer, default=1)  # 1=abilitato, 0=disabilitato
    auto_approve_threshold = Column(Float, default=0.8)  # Soglia per approvazione automatica
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DailyPostSettings(Base):
    """Impostazioni per il post giornaliero di riepilogo."""
    __tablename__ = "daily_post_settings"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Integer, default=1)  # 1=abilitato, 0=disabilitato
    post_time = Column(String, default="20:00")  # Orario del post (HH:MM)
    style = Column(Enum(DailyPostStyle), default=DailyPostStyle.CAROUSEL, nullable=False)
    max_messages = Column(Integer, default=20)  # Max messaggi nel post giornaliero
    title_template = Column(String, default="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫")
    hashtag_template = Column(String, default="#spotted #instaspotter #dailyrecap")
    ai_model = Column(Enum(AIModel), default=AIModel.GEMINI, nullable=False)  # AI model per generare contenuti
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DailyPost(Base):
    """Singoli post giornalieri creati."""
    __tablename__ = "daily_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    hashtags = Column(String, default="")
    ai_model_used = Column(Enum(AIModel), nullable=True)  # AI model utilizzato per generare il contenuto
    status = Column(String, default="draft")  # draft, scheduled, published, failed
    scheduled_for = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    image_count = Column(Integer, default=0)
    messages_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_by = Column(String, nullable=True)  # Username dell'utente che ha creato il post
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazione con i messaggi inclusi (opzionale)
    message_ids = Column(String, nullable=True)  # JSON string di ID messaggi inclusi

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

def get_technical_user(db: Session, technical_user_id: str) -> Optional[TechnicalUser]:
    """Recupera un utente tecnico dal suo ID."""
    return db.query(TechnicalUser).filter(TechnicalUser.id == technical_user_id).first()

def create_technical_user(db: Session) -> TechnicalUser:
    """Crea un nuovo utente tecnico con un UUID."""
    new_user = TechnicalUser(id=str(uuid.uuid4()))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_or_create_technical_user(db: Session, technical_user_id: Optional[str]) -> Tuple[TechnicalUser, bool]:
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

# --- Funzioni per il Daily Post ---

def get_daily_post_settings(db: Session) -> Optional[DailyPostSettings]:
    """Recupera le impostazioni del post giornaliero."""
    return db.query(DailyPostSettings).first()

def update_daily_post_settings(db: Session, **kwargs) -> DailyPostSettings:
    """Aggiorna le impostazioni del post giornaliero."""
    settings = get_daily_post_settings(db)
    if not settings:
        settings = DailyPostSettings(
            enabled=True,  # Abilita di default
            post_time="20:00",
            style="carousel",
            max_messages=20,
            title_template="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫",
            hashtag_template="#spotted #instaspotter #dailyrecap",
            ai_model=AIModel.GEMINI
        )
        db.add(settings)

    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings

def get_todays_messages(db: Session, limit: int = 20) -> list:
    """Recupera tutti i messaggi APPROVED di oggi."""
    from datetime import datetime, time

    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_end = datetime.combine(datetime.utcnow().date(), time.max)

    return db.query(SpottedMessage).filter(
        SpottedMessage.status == MessageStatus.APPROVED,
        SpottedMessage.created_at >= today_start,
        SpottedMessage.created_at <= today_end
    ).order_by(SpottedMessage.created_at).limit(limit).all()

def mark_daily_post_run(db: Session):
    """Marca che il post giornaliero è stato eseguito oggi."""
    settings = get_daily_post_settings(db)
    if settings:
        settings.last_run = datetime.utcnow()
        db.commit()

# --- Funzioni per l'AI Config ---

def get_ai_config(db: Session) -> Optional[AIConfig]:
    """Recupera la configurazione AI."""
    return db.query(AIConfig).first()

def update_ai_config(db: Session, **kwargs) -> AIConfig:
    """Aggiorna la configurazione AI."""
    config = get_ai_config(db)
    if not config:
        config = AIConfig()
        db.add(config)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return config

# --- Funzioni per Daily Posts Management ---

def create_daily_post(db: Session, title: str, content: str, hashtags: str = "", ai_model_used: AIModel = None, created_by: str = None) -> DailyPost:
    """Crea un nuovo daily post."""
    daily_post = DailyPost(
        title=title,
        content=content,
        hashtags=hashtags,
        ai_model_used=ai_model_used,
        created_by=created_by,
        status="draft"
    )
    db.add(daily_post)
    db.commit()
    db.refresh(daily_post)
    return daily_post

def get_daily_posts(db: Session, limit: int = 50, status: str = None) -> list:
    """Recupera tutti i daily posts con filtri opzionali."""
    query = db.query(DailyPost).order_by(DailyPost.created_at.desc())

    if status:
        query = query.filter(DailyPost.status == status)

    return query.limit(limit).all()

def get_daily_post_by_id(db: Session, post_id: int) -> Optional[DailyPost]:
    """Recupera un daily post per ID."""
    return db.query(DailyPost).filter(DailyPost.id == post_id).first()

def update_daily_post(db: Session, post_id: int, **kwargs) -> Optional[DailyPost]:
    """Aggiorna un daily post."""
    post = get_daily_post_by_id(db, post_id)
    if not post:
        return None

    for key, value in kwargs.items():
        if hasattr(post, key):
            setattr(post, key, value)

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post

def delete_daily_post(db: Session, post_id: int) -> bool:
    """Elimina un daily post."""
    post = get_daily_post_by_id(db, post_id)
    if not post:
        return False

    db.delete(post)
    db.commit()
    return True

def get_published_daily_posts(db: Session, limit: int = 20) -> list:
    """Recupera i daily posts pubblicati."""
    return db.query(DailyPost).filter(
        DailyPost.status == "published"
    ).order_by(DailyPost.published_at.desc()).limit(limit).all()
