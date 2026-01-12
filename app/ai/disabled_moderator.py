from app.ai.moderator import AIModerator, ModerationResult

class DisabledModerator(AIModerator):
    """Moderatore disabilitato - tutti i messaggi vanno in pending."""

    def moderate_message(self, message: str) -> ModerationResult:
        """Sempre restituisce PENDING - moderazione disabilitata."""
        return ModerationResult(
            decision="PENDING",
            reason="Moderazione AI disabilitata - richiede approvazione manuale",
            confidence=0.0
        )

    def is_available(self) -> bool:
        """Sempre disponibile (disabilitato)."""
        return True
