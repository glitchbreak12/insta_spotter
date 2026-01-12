from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class ModerationResult:
    decision: str  # "APPROVE", "REJECT", "PENDING"
    reason: str
    confidence: float = 0.0

class AIModerator(ABC):
    """Classe base astratta per i moderatori AI."""

    @abstractmethod
    def moderate_message(self, message: str) -> ModerationResult:
        """Modera un messaggio e restituisce il risultato."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se il moderatore è disponibile."""
        pass

class AIModeratorFactory:
    """Factory per creare istanze di moderatori AI basati sulla configurazione."""

    @staticmethod
    def create_moderator(model_type: str, **kwargs) -> Optional[AIModerator]:
        """Crea un moderatore basato sul tipo di modello."""
        if model_type == "gemini":
            try:
                from app.ai.gemini_moderator import GeminiModerator
                return GeminiModerator(api_key=kwargs.get('api_key'))
            except Exception as e:
                print(f"❌ Errore creazione GeminiModerator: {e}")
                return None
        elif model_type == "grok":
            try:
                from app.ai.grok_moderator import GrokModerator
                return GrokModerator(api_key=kwargs.get('api_key'))
            except Exception as e:
                print(f"❌ Errore creazione GrokModerator: {e}")
                return None
        elif model_type == "local":
            try:
                from app.ai.local_moderator import LocalModerator
                return LocalModerator(model_path=kwargs.get('model_path'))
            except Exception as e:
                print(f"❌ Errore creazione LocalModerator: {e}")
                return None
        elif model_type == "disabled":
            from app.ai.disabled_moderator import DisabledModerator
            return DisabledModerator()

        return None