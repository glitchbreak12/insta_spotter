import os
from typing import Optional
from app.ai.moderator import AIModerator, ModerationResult

class GrokModerator(AIModerator):
    """Moderatore basato su Grok AI (xAI)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.client = None

        if self.api_key:
            try:
                # Nota: Questa è una implementazione di esempio.
                # Dovresti usare la libreria ufficiale di xAI quando disponibile
                print("🔧 GrokModerator inizializzato (simulazione)")
            except Exception as e:
                print(f"❌ Errore inizializzazione Grok: {e}")

    def moderate_message(self, message: str) -> ModerationResult:
        """Modera un messaggio usando Grok AI."""
        if not self.is_available():
            return ModerationResult(
                decision="PENDING",
                reason="Grok AI non disponibile",
                confidence=0.0
            )

        try:
            # Simulazione della moderazione Grok
            # In produzione, implementare la vera chiamata API

            # Analisi semplice basata su parole chiave
            lower_message = message.lower()

            # Parole chiave negative
            negative_words = ['odio', 'violenza', 'razzismo', 'discriminazione', 'insulto']
            positive_indicators = ['grazie', 'bello', 'fantastico', 'amore', 'amicizia']

            negative_score = sum(1 for word in negative_words if word in lower_message)
            positive_score = sum(1 for word in positive_indicators if word in lower_message)

            if negative_score > 0:
                return ModerationResult(
                    decision="REJECT",
                    reason="Contenuto potenzialmente offensivo rilevato",
                    confidence=0.7
                )
            elif positive_score > 0 or len(message.strip()) > 10:
                return ModerationResult(
                    decision="APPROVE",
                    reason="Contenuto positivo o sufficientemente lungo",
                    confidence=0.8
                )
            else:
                return ModerationResult(
                    decision="PENDING",
                    reason="Contenuto neutro - richiede revisione manuale",
                    confidence=0.5
                )

        except Exception as e:
            return ModerationResult(
                decision="PENDING",
                reason=f"Errore Grok AI: {str(e)}",
                confidence=0.0
            )

    def is_available(self) -> bool:
        """Verifica se Grok è disponibile."""
        return bool(self.api_key)
