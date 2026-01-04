from app.image.generator import ImageGenerator
from config import settings

# --- Configurazione ---
# Assicurati che il template_path in config.py sia impostato su card_v3.html
settings.image.template_path = "app/image/templates/card_v3.html"

# --- Generazione anteprima ---
generator = ImageGenerator()
test_message = "Questa è un'anteprima della card aggiornata. Il layout è stato migliorato e ora include una call to action."
image_path = generator.from_text(test_message, "preview_card_v3.png", 999)

if image_path:
    print(f"Immagine di anteprima generata in: {image_path}")
    print("Aprila per vedere il risultato e fammi sapere se ti piace.")
else:
    print("Errore durante la generazione dell'anteprima.")