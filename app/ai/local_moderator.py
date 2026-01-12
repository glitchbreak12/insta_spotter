import os
from typing import Optional
from app.ai.moderator import AIModerator, ModerationResult

class LocalModerator(AIModerator):
    """Moderatore basato su modello locale (es. BERT, DistilBERT)."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("LOCAL_MODEL_PATH")
        self.model = None

        if self.model_path and os.path.exists(self.model_path):
            try:
                # Simulazione caricamento modello locale
                print(f"🔧 LocalModerator inizializzato con modello: {self.model_path}")
                self.model = "loaded"  # Placeholder
            except Exception as e:
                print(f"❌ Errore caricamento modello locale: {e}")
        else:
            print("⚠️ Modello locale non trovato - usando logica semplificata")

    def moderate_message(self, message: str) -> ModerationResult:
        """Modera un messaggio usando modello locale."""
        if not self.is_available():
            return ModerationResult(
                decision="PENDING",
                reason="Modello locale non disponibile",
                confidence=0.0
            )

        try:
            # Logica semplificata per moderazione locale
            lower_message = message.lower()

            # Analisi basata su lunghezza e contenuto
            if len(message.strip()) < 5:
                return ModerationResult(
                    decision="REJECT",
                    reason="Messaggio troppo corto",
                    confidence=0.9
                )

            # Parole chiave problematiche
            problematic_words = ['spam', 'fake', 'scam', 'inappropriate']
            has_problems = any(word in lower_message for word in problematic_words)

            if has_problems:
                return ModerationResult(
                    decision="REJECT",
                    reason="Contenuto problematico rilevato",
                    confidence=0.8
                )

            # Controllo qualità contenuto
            if len(message.strip()) > 20 and not has_problems:
                return ModerationResult(
                    decision="APPROVE",
                    reason="Contenuto di qualità sufficiente",
                    confidence=0.7
                )
            else:
                return ModerationResult(
                    decision="PENDING",
                    reason="Richiede revisione manuale",
                    confidence=0.5
                )

        except Exception as e:
            return ModerationResult(
                decision="PENDING",
                reason=f"Errore modello locale: {str(e)}",
                confidence=0.0
            )

    def is_available(self) -> bool:
        """Verifica se il modello locale è disponibile."""
        return self.model is not None or not self.model_path
