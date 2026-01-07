import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# --- Impostazioni Principali ---

class InstagramSettings(BaseModel):
    """Configurazioni per l'account Instagram."""
    username: str = os.getenv("INSTAGRAM_USERNAME", "")
    password: str = os.getenv("INSTAGRAM_PASSWORD", "")
    session_file: str = "data/session.json"

class AutomationSettings(BaseModel):
    """Configurazioni per l'automazione del bot."""
    check_interval_seconds: int = 60  # Controlla nuovi messaggi ogni 60 secondi
    posts_per_hour: int = 10
    autonomous_mode_enabled: bool = False # Nuova impostazione per la modalità autonoma

class DailyPostSettings(BaseModel):
    """Configurazioni per il post giornaliero di riepilogo."""
    enabled: bool = True
    post_time: str = "20:00"  # Orario del post giornaliero (HH:MM)
    style: str = "carousel"  # Stile del post: grid, carousel, compact, elegant
    max_messages: int = 20  # Numero massimo di messaggi nel post giornaliero
    title_template: str = "🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫"
    hashtag_template: str = "#spotted #instaspotter #dailyrecap"

class ImageSettings(BaseModel):
    """Configurazioni per la generazione delle immagini."""
            template_path: str = "app/image/templates/card_v5_fixed.html"  # FORZATO: usa sempre card_v5.html
    output_folder: str = "data/generated_images"
    width: int = 1080
    height: int = 1920

class WebSettings(BaseModel):
    """Configurazioni per l'interfaccia web."""
    host: str = "127.0.0.1"
    port: int = 8000

class DatabaseSettings(BaseModel):
    """Configurazioni per il database."""
    # Usa DATABASE_URL se disponibile (per Render), altrimenti usa SQLite locale.
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///data/messages.db")

class Settings(BaseModel):
    """Contenitore globale per tutte le configurazioni."""
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instagram: InstagramSettings = InstagramSettings()
    automation: AutomationSettings = AutomationSettings()
    daily_post: DailyPostSettings = DailyPostSettings()
    image: ImageSettings = ImageSettings()
    web: WebSettings = WebSettings()
    database: DatabaseSettings = DatabaseSettings()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "") # New: Gemini API Key

# Istanza globale delle impostazioni, da importare negli altri file
settings = Settings()

# --- Funzioni di Utilità ---

def ensure_directories_exist():
    """Assicura che le cartelle necessarie esistano."""
    os.makedirs(settings.image.output_folder, exist_ok=True)
    os.makedirs(os.path.dirname(settings.instagram.session_file), exist_ok=True)

# Esegui la funzione all'avvio per creare le cartelle
ensure_directories_exist()
