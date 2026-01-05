from instagrapi import Client
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ChallengeRequired
from instagrapi.types import ChallengeChoice
import os
import time

from config import settings

class InstagramBot:
    """Gestisce le interazioni con l'API di Instagram."""

    def __init__(self):
        self.client = Client()
        self.client.set_settings({
            "user_agent": "Instagram 27.0.0.7.97 Android (24/7.0; 380dpi; 1080x1920; OnePlus; ONEPLUS A3010; OnePlus3T; qcom; en_US)",
            "accept_language": "en-US",
            "app_id": "936619743392459",
            "app_version": "27.0.0.7.97",
            "ig_capabilities": "3brTvw==",
            "ig_connection_type": "WIFI",
            "ig_connection_speed": "1200kbps",
            "timezone_offset": "2",
        })
        self.username = settings.instagram.username
        self.password = settings.instagram.password
        self.two_factor_seed = os.getenv("TWO_FACTOR_SEED")
        self.session_file = settings.instagram.session_file
        self._login()

    def _login(self):
        """Gestisce il login, caricando la sessione e gestendo la 2FA."""
        if os.path.exists(self.session_file):
            print("--- DEBUG [POSTER]: Trovata sessione esistente, la carico... ---")
            try:
                self.client.load_settings(self.session_file)
                # Valida la sessione con una chiamata leggera
                self.client.get_timeline_feed()  # Valida la sessione
                print("--- DEBUG [POSTER]: Login tramite sessione valido. ---")
                return
            except (LoginRequired, ChallengeRequired) as e:
                print(f"--- DEBUG [POSTER]: Sessione non valida o challenge richiesta: {e}. Eseguo login completo... ---")
            except Exception as e:
                error_str = str(e).lower()
                if "update instagram" in error_str or "latest version" in error_str:
                    print("--- DEBUG [POSTER]: Sessione obsoleta (richiede aggiornamento). Eseguo login completo... ---")
                else:
                    print(f"--- DEBUG [POSTER]: Errore validazione sessione: {e}. Eseguo login completo... ---")
        
        print("--- DEBUG [POSTER]: Eseguo login completo... ---")
        try:
            # Aggiorna le impostazioni prima del login per usare versioni più recenti
            self.client.set_settings({
                "user_agent": "Instagram 319.0.0.27.95 Android (24/7.0; 380dpi; 1080x1920; samsung; SM-G998B; o1s; en_US)",
                "accept_language": "en-US",
                "app_id": "936619743392459",
                "app_version": "319.0.0.27.95",
                "ig_capabilities": "3brTvwE=",
                "ig_connection_type": "WIFI",
                "ig_connection_speed": "1200kbps",
                "timezone_offset": "2",
            })
            
            self.client.login(self.username, self.password)
        except ChallengeRequired as e:
            print("--- DEBUG [POSTER]: Instagram richiede verifica (Challenge). ---")
            print(f"--- DEBUG [POSTER]: Challenge info: {e} ---")
            
            # Prova a risolvere la challenge automaticamente
            try:
                # Scegli EMAIL come metodo di verifica (più comune)
                challenge_choice = ChallengeChoice.EMAIL
                print(f"--- DEBUG [POSTER]: Scelto metodo di verifica: {challenge_choice} ---")
                
                # Invia la richiesta di codice
                self.client.challenge_select_method(challenge_choice)
                print("--- DEBUG [POSTER]: Richiesta codice di verifica inviata. ---")
                print("--- DEBUG [POSTER]: Controlla la tua email per il codice a 6 cifre. ---")
                
                # Controlla se c'è un codice pre-configurato nei Secrets
                verification_code = os.getenv("INSTAGRAM_VERIFICATION_CODE")
                
                if verification_code and len(verification_code) == 6:
                    print(f"--- DEBUG [POSTER]: Trovato codice di verifica nei Secrets. ---")
                    self.client.challenge_code_handler(verification_code)
                    print("--- DEBUG [POSTER]: Verifica completata con codice dai Secrets. ---")
                else:
                    # Se non c'è codice, salva le info della challenge e solleva un errore informativo
                    print("--- DEBUG [POSTER]: Nessun codice di verifica trovato nei Secrets. ---")
                    print("--- DEBUG [POSTER]: Aggiungi INSTAGRAM_VERIFICATION_CODE nei Secrets di Replit. ---")
                    print("--- DEBUG [POSTER]: Il codice è stato inviato alla tua email. ---")
                    raise Exception(
                        "Instagram richiede verifica via email. "
                        "Controlla la tua email per il codice a 6 cifre, poi aggiungilo come "
                        "INSTAGRAM_VERIFICATION_CODE nei Secrets di Replit e riavvia l'app."
                    )
                    
            except Exception as challenge_error:
                print(f"--- DEBUG [POSTER]: Errore durante la gestione della challenge: {challenge_error} ---")
                raise
                
        except TwoFactorRequired:
            print("--- DEBUG [POSTER]: Richiesta 2FA. ---")
            if not self.two_factor_seed:
                print("--- DEBUG [POSTER]: ERRORE CRITICO: 2FA richiesta ma TWO_FACTOR_SEED non impostato in .env ---")
                raise Exception("2FA richiesta, ma il seed non è configurato.")
            
            code = self.client.two_factor_login_code(self.two_factor_seed)
            print(f"--- DEBUG [POSTER]: Codice 2FA generato: {code}. Tento il login 2FA... ---")
            self.client.two_factor_login(code)
        except Exception as e:
            print(f"--- DEBUG [POSTER]: ERRORE durante il login: {e} ---")
            raise
        
        print("--- DEBUG [POSTER]: Login completato. Salvo la sessione... ---")
        self.client.dump_settings(self.session_file)

    def post_story(self, image_path: str) -> bool:
        if not os.path.exists(image_path): return False
        try:
            print(f"--- DEBUG [POSTER]: Tento pubblicazione storia: {image_path} ---")
            media = self.client.photo_upload_to_story(path=image_path)
            if not media:
                print("--- DEBUG [POSTER]: ERRORE: La pubblicazione potrebbe essere fallita (nessun oggetto media restituito). ---")
                return None
            print("--- DEBUG [POSTER]: Storia pubblicata con successo! ---")
            return media.pk
        except Exception as e:
            error_str = str(e)
            print(f"--- DEBUG [POSTER]: ERRORE pubblicazione storia: {error_str} ---")
            
            # Rileva vari tipi di errori che richiedono un nuovo login
            needs_relogin = (
                isinstance(e, LoginRequired) or
                isinstance(e, ChallengeRequired) or
                "update Instagram to the latest version" in error_str.lower() or
                "login required" in error_str.lower() or
                "session" in error_str.lower() and "expired" in error_str.lower()
            )
            
            if needs_relogin:
                print("--- DEBUG [POSTER]: Sessione scaduta o obsoleta. Rimuovo il file di sessione... ---")
                if os.path.exists(self.session_file):
                    os.remove(self.session_file)
                    print("--- DEBUG [POSTER]: File di sessione rimosso. Provo un nuovo login... ---")
                
                # Tenta un nuovo login e riprova una volta
                try:
                    print("--- DEBUG [POSTER]: Tentativo di nuovo login... ---")
                    self._login()
                    print("--- DEBUG [POSTER]: Nuovo login completato. Riprovo la pubblicazione... ---")
                    media = self.client.photo_upload_to_story(path=image_path)
                    if media:
                        print("--- DEBUG [POSTER]: Storia pubblicata con successo dopo nuovo login! ---")
                        return media.pk
                except Exception as retry_error:
                    print(f"--- DEBUG [POSTER]: Errore anche dopo nuovo login: {retry_error} ---")
            
            return None

    def post_album(self, image_paths: list[str], caption: str) -> bool:
        if not image_paths: return False
        try:
            print(f"--- DEBUG [POSTER]: Tento pubblicazione album con {len(image_paths)} immagini... ---")
            self.client.album_upload(paths=image_paths, caption=caption)
            print("--- DEBUG [POSTER]: Album pubblicato con successo! ---")
            return self.client.last_json['media']['pk']
        except Exception as e:
            print(f"--- DEBUG [POSTER]: ERRORE pubblicazione album: {e} ---")
            if isinstance(e, LoginRequired):
                if os.path.exists(self.session_file): os.remove(self.session_file)
            return None

    def get_media_comments(self, media_pk: str) -> list[dict] | None:
        """
        Recupera i commenti per un dato media_pk di Instagram.

        Args:
            media_pk: L'ID del media di Instagram (post o storia).

        Returns:
            Una lista di dizionari, ognuno rappresentante un commento, o None in caso di errore.
        """
        try:
            print(f"--- DEBUG [POSTER]: Recupero commenti per media PK: {media_pk} ---")
            comments = self.client.media_comments(media_pk)
            print(f"--- DEBUG [POSTER]: Trovati {len(comments)} commenti per media PK: {media_pk} ---")
            # Converti gli oggetti Comment in dizionari per una facile serializzazione
            return [comment.dict() for comment in comments]
        except Exception as e:
            print(f"--- DEBUG [POSTER]: ERRORE recupero commenti per media PK {media_pk}: {e} ---")
            return None