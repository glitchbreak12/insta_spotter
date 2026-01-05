# Usa il vecchio pacchetto google-generativeai (più stabile e funzionante)
# Il nuovo google-genai ha un'API completamente diversa e non è ancora stabile
try:
    import google.generativeai as genai
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")
except ImportError:
    # Se non è installato, solleverà un errore più chiaro
    genai = None
import json
from config import settings
from typing import NamedTuple

# --- Struttura per la Risposta di Moderazione ---
class ModerationResult(NamedTuple):
    """
    Contiene il risultato strutturato della moderazione AI.
    """
    decision: str  # "APPROVE", "REJECT", "PENDING"
    reason: str    # Spiegazione della decisione
    category: str  # Categoria del contenuto (es. "Safe", "Insult", "Link")

class GeminiModerator:
    """
    Modera i messaggi utilizzando il modello Gemini con regole specifiche.
    """
    def __init__(self):
        if genai is None:
            raise ImportError("google-generativeai package not installed. Install it with: pip install google-generativeai")
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=settings.gemini_api_key)
        
        # Istruzioni dettagliate per il modello IA
        system_prompt = """
Sei un moderatore di contenuti per una pagina Instagram anonima chiamata "InstaSpotter".
Il tuo compito è analizzare i messaggi inviati dagli utenti e decidere se approvarli, rifiutarli o metterli in attesa per una revisione umana.

Le tue decisioni devono seguire queste regole in modo ferreo:

1.  **RIFIUTA (REJECT) SEMPRE E IMMEDIATAMENTE per queste violazioni:**
    - **Link/URL:** Qualsiasi testo che contenga "http", "https", "www", ".com", ".it", ".org", o qualsiasi altro formato di link.
    - **Insulti/Odio:** Linguaggio volgare, offensivo, incitamento all'odio, bullismo, attacchi personali.
    - **Pubblicità/Sponsor:** Messaggi che promuovono prodotti, servizi, o altri canali social.
    - **Spam/Testo Casuale:** Testo senza senso, ripetizioni di caratteri, gibberish.

2.  **APPROVA (APPROVE) i messaggi che sono chiaramente sicuri e rientrano nello scopo della pagina:**
    - Messaggi "spotted" classici (es. "Spotto ragazza vista in piazza...", "Spotto ragazzo con la felpa blu...").
    - Ricerche di persone per motivi non malevoli (es. "Cerco qualcuno che era al concerto...").
    - Pensieri o confessioni anonime che non violano altre regole.

3.  **METTI IN ATTESA (PENDING) se sei insicuro:**
    - Se un messaggio è ambiguo, al limite, o potrebbe essere interpretato in modi diversi.
    - Se non sei sicuro al 100% che sia sicuro o che violi una regola.
    - Usa questa opzione come misura di sicurezza per far decidere un umano.

**FORMATO DELLA RISPOSTA:**
La tua risposta DEVE essere un oggetto JSON, e solo JSON, senza testo aggiuntivo.
L'oggetto JSON deve avere questa struttura:
{
  "decision": "...",
  "reason": "...",
  "category": "..."
}

**Valori possibili per i campi:**
- `decision`: Una delle tre stringhe: "APPROVE", "REJECT", "PENDING".
- `reason`: Una frase breve e chiara che spiega la tua decisione.
- `category`: Una delle seguenti categorie: "Safe", "Link", "Insult", "Spam", "Advertisement", "Uncertain".

**Esempio 1:**
Messaggio: "Spotto la ragazza con il cappotto rosso che ho visto oggi in biblioteca, mi hai sorriso!"
Tua Risposta:
{
  "decision": "APPROVE",
  "reason": "Messaggio spotted standard e sicuro.",
  "category": "Safe"
}

**Esempio 2:**
Messaggio: "Visitate il mio nuovo sito www.esempio.com per vincere premi!"
Tua Risposta:
{
  "decision": "REJECT",
  "reason": "Il messaggio contiene un link, che è vietato.",
  "category": "Link"
}

**Esempio 3:**
Messaggio: "Marco sei un cretino, quello che hai fatto non si fa."
Tua Risposta:
{
  "decision": "REJECT",
  "reason": "Il messaggio contiene un insulto personale.",
  "category": "Insult"
}

**Esempio 4:**
Messaggio: "Sto cercando di organizzare una cosa per beneficenza, non so se questo è il posto giusto."
Tua Risposta:
{
  "decision": "PENDING",
  "reason": "Il messaggio sembra a fin di bene ma potrebbe non essere in linea con lo scopo della pagina. Richiede revisione umana.",
  "category": "Uncertain"
}
"""
        
        # Usa gemini-pro che è più stabile e disponibile gratuitamente
        # gemini-1.5-pro potrebbe non essere disponibile per tutti gli account
        try:
            self.model = genai.GenerativeModel(
                'gemini-pro',
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
                system_instruction=system_prompt
            )
        except Exception as e:
            # Fallback a gemini-1.5-flash se gemini-pro non è disponibile
            print(f"--- [Moderator] Tentativo con gemini-pro fallito: {e}. Provo con gemini-1.5-flash ---")
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                ),
                system_instruction=system_prompt
            )

    def moderate_message(self, text: str) -> ModerationResult:
        """
        Invia il testo al modello Gemini per la moderazione e restituisce un risultato strutturato.
        """
        try:
            prompt = f"Analizza il seguente messaggio: \"{text}\""
            response = self.model.generate_content(prompt)
            
            # Pulisci e carica il JSON dalla risposta del modello
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(response_text)
            
            # Assicura che la decisione sia uno dei valori attesi
            decision = data.get("decision", "PENDING").upper()
            if decision not in ["APPROVE", "REJECT", "PENDING"]:
                decision = "PENDING"

            return ModerationResult(
                decision=decision,
                reason=data.get("reason", "Analisi AI non conclusiva."),
                category=data.get("category", "Uncertain")
            )
        except Exception as e:
            print(f"--- ERRORE [Moderator]: Impossibile analizzare il messaggio. Errore: {e} ---")
            # In caso di errore, metti in pending per sicurezza
            return ModerationResult(
                decision="PENDING",
                reason=f"Errore tecnico durante l'analisi AI: {e}",
                category="Error"
            )

# Esempio di utilizzo (per testare questo file singolarmente)
if __name__ == '__main__':
    moderator = GeminiModerator()
    
    test_messages = [
        "Spotto un ragazzo altissimo con gli occhiali alla fermata del bus stamattina. Aveva uno zaino verde.",
        "Comprate subito i nuovi integratori su www.superfit.com, sono i migliori!",
        "Marco sei un cretino, quello che hai fatto non si fa.",
        "asdfghjkl asdfghjkl qwertyuiop",
        "Vorrei trovare la ragazza che ha perso questo braccialetto al parco ieri."
    ]
    
    for msg in test_messages:
        result = moderator.moderate_message(msg)
        print(f"Messaggio: '{msg}'")
        print(f"  -> Decisione: {result.decision}, Motivo: {result.reason}, Categoria: {result.category}\n")