import imgkit
import jinja2
import os
from pathlib import Path
from config import settings

class ImageGenerator:
    """Gestisce la creazione di immagini per le storie di Instagram."""

    def __init__(self):
        # --- Configurazione dinamica del percorso di wkhtmltoimage ---
        if os.name == 'nt': # 'nt' è il nome per Windows
            # Percorso per l'installazione predefinita su Windows
            path_wkhtmltoimage = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe'
            self.config = imgkit.config(wkhtmltoimage=path_wkhtmltoimage)
        else:
            # Su Linux (come in Render), il percorso è solitamente questo
            # Render include già wkhtmltoimage nel suo ambiente standard
            self.config = {}
        # --------------------------------------------------

        # Configura il loader di Jinja2 per trovare i template nella cartella corretta
        self.template_base_dir = os.path.dirname(settings.image.template_path)
        self.template_loader = jinja2.FileSystemLoader(searchpath=self.template_base_dir)
        self.template_env = jinja2.Environment(loader=self.template_loader)
        self.output_folder = settings.image.output_folder
        self.image_width = settings.image.width


        # Assicura che la cartella di output esista
        os.makedirs(self.output_folder, exist_ok=True)

    def _render_html(self, message_text: str, message_id: int) -> str:
        """Carica il template HTML e inserisce il messaggio e l'URL del font."""
        template = self.template_env.get_template(os.path.basename(settings.image.template_path))
        
        # Crea un URL assoluto e corretto per il file del font
        font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
        font_url = Path(font_path).as_uri()

        return template.render(message=message_text, id=message_id, font_url=font_url)

    def from_text(self, message_text: str, output_filename: str, message_id: int) -> str | None:
        """
        Genera un'immagine PNG da un testo utilizzando un template HTML.

        Args:
            message_text: Il testo da inserire nell'immagine.
            output_filename: Il nome del file di output (es. 'spotted_123.png').
            message_id: L'ID del messaggio, da passare al template.

        Returns:
            Il percorso del file generato, o None se si verifica un errore.
        """
        try:
            # Renderizza l'HTML con il messaggio e il percorso base
            html_content = self._render_html(message_text, message_id)

            # Definisce il percorso completo per il file di output
            output_path = os.path.join(self.output_folder, output_filename)

            # Opzioni per imgkit: larghezza, qualità, e abilitazione accesso file locali
            options = {
                'width': self.image_width,
                'encoding': "UTF-8",
                'enable-local-file-access': None, # Necessario per caricare font locali
                'quiet': '' # Sopprime l'output di wkhtmltoimage
            }

            # Genera l'immagine dall'HTML
            imgkit.from_string(html_content, output_path, options=options, config=self.config)

            print(f"Immagine generata con successo: {output_path}")
            return output_path

        except Exception as e:
            # Qui gestiamo il potenziale errore se wkhtmltoimage non è installato
            if "No wkhtmltoimage executable found" in str(e):
                print("\n---")
                print("ERRORE CRITICO: `wkhtmltoimage` non trovato.")
                print("Per generare le immagini, questo programma esterno è necessario.")
                print("Installalo da: https://wkhtmltopdf.org/downloads.html")
                print("Dopo l'installazione, potrebbe essere necessario riavviare.")
                print("---\n")
            else:
                print(f"Errore imprevisto durante la generazione dell'immagine: {e}")
            return None

# Esempio di utilizzo (per testare questo file singolarmente)
if __name__ == '__main__':
    generator = ImageGenerator()
    test_message = "Ho spottato una ragazza con un libro di poesie alla fermata del 17. Mi ha sorriso e ha reso la mia giornata migliore. Chissà se leggerà mai questo messaggio."
    
    # Genera l'immagine
    image_path = generator.from_text(test_message, "test_card.png", 1)

    if image_path:
        print(f"\nTest completato. Immagine di prova creata in: {image_path}")
        print("Aprila per vedere il risultato!")