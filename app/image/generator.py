import imgkit
import jinja2
import os
from pathlib import Path
from config import settings

# Import per fallback con PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ImageGenerator:
    """Gestisce la creazione di immagini per le storie di Instagram."""

    def __init__(self):
        # --- Configurazione dinamica del percorso di wkhtmltoimage ---
        if os.name == 'nt': # 'nt' è il nome per Windows
            # Percorso per l'installazione predefinita su Windows
            path_wkhtmltoimage = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe'
            self.config = imgkit.config(wkhtmltoimage=path_wkhtmltoimage)
        else:
            # Su Linux (Replit, Render, etc.)
            # Prova a trovare wkhtmltoimage nel PATH
            import shutil
            wkhtmltoimage_path = shutil.which('wkhtmltoimage')
            if wkhtmltoimage_path:
                self.config = imgkit.config(wkhtmltoimage=wkhtmltoimage_path)
                print(f"✓ wkhtmltoimage trovato: {wkhtmltoimage_path}")
            else:
                # Se non trovato, prova percorsi comuni
                common_paths = [
                    '/usr/bin/wkhtmltoimage',
                    '/usr/local/bin/wkhtmltoimage',
                    '/bin/wkhtmltoimage'
                ]
                found = False
                for path in common_paths:
                    if os.path.exists(path):
                        self.config = imgkit.config(wkhtmltoimage=path)
                        print(f"✓ wkhtmltoimage trovato: {path}")
                        found = True
                        break
                
                if not found:
                    # Configurazione vuota - imgkit userà il PATH
                    self.config = {}
                    print("⚠ wkhtmltoimage non trovato nel PATH. Assicurati che sia installato.")
        # --------------------------------------------------

        # Configura il loader di Jinja2 per trovare i template nella cartella corretta
        self.template_base_dir = os.path.dirname(settings.image.template_path)
        self.template_loader = jinja2.FileSystemLoader(searchpath=self.template_base_dir)
        self.template_env = jinja2.Environment(loader=self.template_loader)
        self.output_folder = settings.image.output_folder
        self.image_width = settings.image.width


        # Assicura che la cartella di output esista
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Verifica se wkhtmltoimage è disponibile
        import shutil
        self.wkhtmltoimage_available = bool(shutil.which('wkhtmltoimage'))
        
        # Se wkhtmltoimage non è disponibile, usa PIL come fallback
        if not self.wkhtmltoimage_available:
            if PIL_AVAILABLE:
                print("⚠ wkhtmltoimage non disponibile. Uso PIL come fallback.")
            else:
                print("⚠ ATTENZIONE: né wkhtmltoimage né PIL sono disponibili!")
                print("   Installa Pillow: pip install Pillow")

    def _render_html(self, message_text: str, message_id: int) -> str:
        """Carica il template HTML e inserisce il messaggio e l'URL del font."""
        template = self.template_env.get_template(os.path.basename(settings.image.template_path))
        
        # Crea un URL assoluto e corretto per il file del font
        font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
        font_url = Path(font_path).as_uri()

        return template.render(message=message_text, id=message_id, font_url=font_url)

    def _generate_with_pil(self, message_text: str, output_path: str, message_id: int) -> bool:
        """Genera un'immagine con stile Apple 3D semplice e pulito."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            import math
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 80
            
            # === SFONDO GRADIENTE SEMPLICE ===
            img = Image.new('RGB', (width, height), color='#f5f5f7')
            draw = ImageDraw.Draw(img)
            
            # Gradiente verticale semplice (bianco -> grigio chiaro)
            for y in range(height):
                progress = y / height
                # Bianco (#f5f5f7) -> grigio chiaro (#e5e5e7)
                r = int(245 - (10 * progress))
                g = int(245 - (10 * progress))
                b = int(247 - (10 * progress))
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # === CARD 3D SEMPLICE (stile Apple) ===
            card_x = padding
            card_y = padding + 100
            card_w = width - (padding * 2)
            card_h = height - (padding * 2) - 200
            
            # Ombra card (semplice)
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            
            # Ombra morbida
            for i in range(15):
                alpha = int(20 - (i * 1.2))
                shadow_draw.rectangle(
                    [card_x + i, card_y + i + 8, 
                     card_x + card_w + i, card_y + card_h + i + 8],
                    fill=(0, 0, 0, alpha)
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Card principale (bianco con bordi arrotondati simulati)
            # Sfondo card
            draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill='#ffffff',
                outline='#d1d1d6',
                width=2
            )
            
            # Highlight superiore (effetto 3D)
            highlight_y = card_y + 2
            for i in range(3):
                alpha = 30 - (i * 10)
                draw.rectangle(
                    [card_x + 2, highlight_y + i, card_x + card_w - 2, highlight_y + i + 1],
                    fill=(255, 255, 255, alpha)
                )
            
            # === CARICA FONT ===
            font_path = os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf')
            try:
                if os.path.exists(font_path):
                    brand_font = ImageFont.truetype(font_path, 110)
                    message_font = ImageFont.truetype(font_path, 64)
                    id_font = ImageFont.truetype(font_path, 32)
                    footer_font = ImageFont.truetype(font_path, 34)
                else:
                    raise FileNotFoundError
            except:
                try:
                    brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
                    message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)
                    id_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                    footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
                except:
                    brand_font = ImageFont.load_default()
                    message_font = ImageFont.load_default()
                    id_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()
            
            # === BRANDING "SPOTTED" SEMPLICE ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 120
            
            # Ombra leggera
            draw.text((brand_x + 2, brand_y + 2), brand_text, fill='#e0e0e0', font=brand_font)
            # Testo principale
            draw.text((brand_x, brand_y), brand_text, fill='#1d1d1f', font=brand_font)
            
            # === ID POST "sp#ID" ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + 130
            
            draw.text((id_x, id_y), id_text, fill='#8e8e93', font=id_font)
            
            # === MESSAGGIO CON WORD WRAP ===
            message_y = id_y + 80
            max_width = card_w - (padding * 2)
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 85
            
            for word in words:
                word_bbox = draw.textbbox((0, 0), word + " ", font=message_font)
                word_width = word_bbox[2] - word_bbox[0]
                
                if current_width + word_width > max_width and current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            if current_line:
                lines.append(" ".join(current_line))
            
            # Disegna messaggio
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_y + i * line_height
                
                # Testo principale
                draw.text((line_x, y_pos), line, fill='#1d1d1f', font=message_font)
            
            # === FOOTER "@spottedatbz" ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 100
            
            draw.text((footer_x, footer_y), footer_text, fill='#8e8e93', font=footer_font)
            
            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata (stile Apple 3D semplice): {output_path}")
            return True
            
        except Exception as e:
            import traceback
            print(f"❌ Errore durante la generazione con PIL: {e}")
            print(traceback.format_exc())
            return False
    
    def from_text(self, message_text: str, output_filename: str, message_id: int) -> str | None:
        """
        Genera un'immagine PNG da un testo utilizzando un template HTML o PIL come fallback.

        Args:
            message_text: Il testo da inserire nell'immagine.
            output_filename: Il nome del file di output (es. 'spotted_123.png').
            message_id: L'ID del messaggio, da passare al template.

        Returns:
            Il percorso del file generato, o None se si verifica un errore.
        """
        # Definisce il percorso completo per il file di output
        output_path = os.path.join(self.output_folder, output_filename)
        
        # Se wkhtmltoimage è disponibile, prova a usarlo
        if self.wkhtmltoimage_available:
            try:
                # Renderizza l'HTML con il messaggio e il percorso base
                html_content = self._render_html(message_text, message_id)

                # Opzioni per imgkit: larghezza, qualità, e abilitazione accesso file locali
                options = {
                    'width': self.image_width,
                    'encoding': "UTF-8",
                    'enable-local-file-access': None, # Necessario per caricare font locali
                    'quiet': '' # Sopprime l'output di wkhtmltoimage
                }

                # Genera l'immagine dall'HTML
                imgkit.from_string(html_content, output_path, options=options, config=self.config)

                print(f"Immagine generata con successo (wkhtmltoimage): {output_path}")
                return output_path

            except Exception as e:
                # Se wkhtmltoimage fallisce, usa PIL come fallback
                if "No wkhtmltoimage executable found" in str(e) or "wkhtmltoimage" in str(e).lower():
                    print("⚠ wkhtmltoimage non disponibile, uso PIL come fallback...")
                    if self._generate_with_pil(message_text, output_path, message_id):
                        return output_path
                else:
                    print(f"Errore con wkhtmltoimage: {e}")
                    print("⚠ Tentativo con PIL come fallback...")
                    if self._generate_with_pil(message_text, output_path, message_id):
                        return output_path
        else:
            # wkhtmltoimage non disponibile, usa direttamente PIL
            if self._generate_with_pil(message_text, output_path, message_id):
                return output_path
        
        # Se arriviamo qui, entrambi i metodi sono falliti
        print("\n---")
        print("ERRORE CRITICO: Impossibile generare l'immagine.")
        print("wkhtmltoimage non disponibile e PIL fallito o non disponibile.")
        print("---\n")
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