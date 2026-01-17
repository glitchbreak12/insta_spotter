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
    images = Column(String, nullable=True)  # JSON array di percorsi immagini per multi-foto



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

def get_or_create_technical_user(db: Session, technical_user_id: Optional[str]) -> TechnicalUser:
    """
    Recupera un utente tecnico se l'ID è valido, altrimenti ne crea uno nuovo.
    Restituisce solo l'utente (non una tupla come prima).
    """
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

    return user

# --- Funzioni per il Daily Post ---

def get_daily_post_settings(db: Session) -> Optional[DailyPostSettings]:
    """Recupera le impostazioni del post giornaliero."""
    return db.query(DailyPostSettings).first()

def update_daily_post_settings(db: Session, **kwargs) -> DailyPostSettings:
    """Aggiorna le impostazioni del post giornaliero."""
    settings = get_daily_post_settings(db)
    if not settings:
        settings = DailyPostSettings(
            enabled=1,  # Abilita di default (1 per integer)
            post_time="20:00",
            max_messages=20,
            title_template="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫",
            hashtag_template="#spotted #instaspotter #dailyrecap",
            ai_model=AIModel.GEMINI
        )
        db.add(settings)

    for key, value in kwargs.items():
        if hasattr(settings, key):
            # Converti boolean a integer per il campo enabled
            if key == "enabled" and isinstance(value, bool):
                setattr(settings, key, 1 if value else 0)
            # Converti stringa a enum per ai_model
            elif key == "ai_model" and isinstance(value, str):
                try:
                    ai_model_enum = AIModel(value)
                    setattr(settings, key, ai_model_enum)
                except ValueError:
                    print(f"⚠️ Modello AI '{value}' non valido, uso GEMINI come default")
                    setattr(settings, key, AIModel.GEMINI)
            else:
                setattr(settings, key, value)

    # Commit changes
    try:
        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        # Handle rare DB insertion errors (eg. NotNullViolation on id in some Postgres setups)
        from sqlalchemy.exc import IntegrityError
        if isinstance(e, IntegrityError):
            db.rollback()
            # Try to fetch again in case of race condition
            existing = get_daily_post_settings(db)
            if existing:
                return existing
            # Fallback: return an in-memory settings object (not persisted) so callers can continue
            print(f"⚠️ Fallback: unable to insert DailyPostSettings due to IntegrityError: {e}")
            temp = DailyPostSettings(
                enabled=1,
                post_time="20:00",
                max_messages=20,
                title_template="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫",
                hashtag_template="#spotted #instaspotter #dailyrecap",
                ai_model=AIModel.GEMINI
            )
            return temp
        else:
            db.rollback()
            raise

def get_todays_messages(db: Session, limit: int = 20) -> list:
    """Recupera tutti i messaggi SPOTTED APPROVED di oggi (esclude INFO cards)."""
    from datetime import datetime, time

    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    today_end = datetime.combine(datetime.utcnow().date(), time.max)

    return db.query(SpottedMessage).filter(
        SpottedMessage.status == MessageStatus.APPROVED,
        SpottedMessage.message_type == MessageType.SPOTTED,  # Solo messaggi spotted, non info cards
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



# --- SYSTEM SETTINGS FUNCTIONS ---

class SystemSetting(Base):
    """Modello per le impostazioni di sistema persistenti."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=True)  # Valore come stringa, convertito in base al tipo
    value_type = Column(String, default="string")  # "string", "boolean", "integer", "float"
    description = Column(String, nullable=True)
    category = Column(String, default="general")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_system_setting(db: Session, key: str) -> Optional[SystemSetting]:
    """Recupera una singola impostazione di sistema."""
    return db.query(SystemSetting).filter(SystemSetting.key == key).first()

def get_all_system_settings(db: Session, category: str = None) -> list:
    """Recupera tutte le impostazioni di sistema, opzionalmente filtrate per categoria."""
    query = db.query(SystemSetting)
    if category:
        query = query.filter(SystemSetting.category == category)
    return query.order_by(SystemSetting.category, SystemSetting.key).all()

def set_system_setting(db: Session, key: str, value: any, value_type: str = "string", description: str = None, category: str = "general") -> SystemSetting:
    """Imposta o aggiorna una impostazione di sistema."""
    setting = get_system_setting(db, key)

    # Converti il valore in stringa per il database
    if value_type == "boolean":
        str_value = "1" if value else "0"
    elif value_type == "integer":
        str_value = str(int(value))
    elif value_type == "float":
        str_value = str(float(value))
    else:
        str_value = str(value) if value is not None else ""

    if setting:
        # Aggiorna impostazione esistente
        setting.value = str_value
        setting.value_type = value_type
        if description:
            setting.description = description
        if category:
            setting.category = category
        setting.updated_at = datetime.utcnow()
    else:
        # Crea nuova impostazione
        setting = SystemSetting(
            key=key,
            value=str_value,
            value_type=value_type,
            description=description,
            category=category
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting

def get_system_setting_value(db: Session, key: str, default_value: any = None) -> any:
    """Recupera il valore di una impostazione di sistema convertito al tipo corretto."""
    setting = get_system_setting(db, key)
    if not setting:
        return default_value

    try:
        if setting.value_type == "boolean":
            return setting.value == "1"
        elif setting.value_type == "integer":
            return int(setting.value)
        elif setting.value_type == "float":
            return float(setting.value)
        else:
            return setting.value
    except (ValueError, TypeError):
        return default_value

def delete_system_setting(db: Session, key: str) -> bool:
    """Elimina una impostazione di sistema."""
    setting = get_system_setting(db, key)
    if not setting:
        return False

    db.delete(setting)
    db.commit()
    return True

# --- UTILITY FUNCTIONS FOR SETTINGS ---

def load_settings_to_environment(db: Session):
    """Carica tutte le impostazioni di sistema nell'ambiente per compatibilità con il codice esistente."""
    settings = get_all_system_settings(db)

    for setting in settings:
        value = get_system_setting_value(db, setting.key)
        if value is not None:
            # Converti in formato compatibile con il codice esistente
            if setting.value_type == "boolean":
                os.environ[setting.key.upper()] = "1" if value else "0"
            else:
                os.environ[setting.key.upper()] = str(value)

def save_environment_to_settings(db: Session):
    """Salva le variabili d'ambiente correnti nelle impostazioni di sistema."""
    # Mappa delle impostazioni chiave -> (tipo, descrizione, categoria)
    env_mapping = {
        "MAINTENANCE_MODE": ("boolean", "Modalità manutenzione abilitata", "system"),
        "MAX_MESSAGES_PER_HOUR": ("integer", "Massimo messaggi per ora", "limits"),
        "SESSION_TIMEOUT": ("integer", "Timeout sessione in ore", "security"),
        "INSTAGRAM_USERNAME": ("string", "Username Instagram", "instagram"),
        "INSTAGRAM_PASSWORD": ("string", "Password Instagram", "instagram"),
        "GEMINI_API_KEY": ("string", "API Key Google Gemini", "ai"),
        "AI_ENABLED": ("boolean", "AI abilitata", "ai"),
        "AI_MODERATION_ENABLED": ("boolean", "Moderazione AI abilitata", "ai"),
        "AI_MODEL": ("string", "Modello AI selezionato", "ai"),
        "AI_AUTO_APPROVE_THRESHOLD": ("float", "Soglia approvazione automatica AI", "ai"),
        "DAILY_POST_ENABLED": ("boolean", "Daily post abilitato", "daily_post"),
        "DAILY_POST_TIME": ("string", "Orario daily post", "daily_post"),
        "DAILY_POST_MAX_MESSAGES": ("integer", "Max messaggi per daily post", "daily_post"),
        "DAILY_POST_TITLE_TEMPLATE": ("string", "Template titolo daily post", "daily_post"),
        "DAILY_POST_HASHTAG_TEMPLATE": ("string", "Template hashtag daily post", "daily_post"),
    }

    for env_key, (value_type, description, category) in env_mapping.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            try:
                if value_type == "boolean":
                    value = env_value.lower() in ("1", "true", "yes", "on")
                elif value_type == "integer":
                    value = int(env_value)
                elif value_type == "float":
                    value = float(env_value)
                else:
                    value = env_value

                set_system_setting(db, env_key.lower(), value, value_type, description, category)
            except (ValueError, TypeError):
                print(f"⚠️ Impossibile convertire {env_key}={env_value} a {value_type}")
