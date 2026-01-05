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
        """Genera l'immagine usando PIL/Pillow con design professionale."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            from PIL import ImageFilter
            import math
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 80
            
            # Crea un'immagine con sfondo gradiente professionale
            img = Image.new('RGB', (width, height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            # Disegna gradiente di sfondo animato (simulato con gradiente diagonale)
            # Colori: #1a1a2e -> #16213e -> #0f3460 (blu scuro elegante)
            for y in range(height):
                # Gradiente verticale con variazione orizzontale per effetto diagonale
                progress = y / height
                x_progress = (y % 200) / 200  # Variazione per effetto animato
                
                # Interpolazione tra i colori del gradiente
                if progress < 0.5:
                    # Prima metà: #1a1a2e -> #16213e
                    r = int(26 + (22 - 26) * progress * 2)
                    g = int(26 + (33 - 26) * progress * 2)
                    b = int(46 + (62 - 46) * progress * 2)
                else:
                    # Seconda metà: #16213e -> #0f3460
                    r = int(22 + (15 - 22) * (progress - 0.5) * 2)
                    g = int(33 + (52 - 33) * (progress - 0.5) * 2)
                    b = int(62 + (96 - 62) * (progress - 0.5) * 2)
                
                # Aggiungi variazione orizzontale per effetto diagonale
                r = max(10, min(255, r + int(math.sin(x_progress * math.pi * 2) * 3)))
                g = max(10, min(255, g + int(math.sin(x_progress * math.pi * 2) * 3)))
                b = max(10, min(255, b + int(math.sin(x_progress * math.pi * 2) * 3)))
                
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Crea un layer per l'effetto glass (sfocatura)
            glass_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glass_draw = ImageDraw.Draw(glass_layer)
            
            # Disegna rettangolo glass con bordi arrotondati (simulato)
            glass_rect = [
                padding, padding,
                width - padding, height - padding
            ]
            
            # Sfondo glass semi-trasparente
            glass_draw.rectangle(glass_rect, fill=(0, 0, 0, 51))  # rgba(0,0,0,0.2)
            
            # Bordo glass
            border_width = 2
            glass_draw.rectangle(
                [glass_rect[0], glass_rect[1], glass_rect[2], glass_rect[3]],
                outline=(255, 255, 255, 26),  # rgba(255,255,255,0.1)
                width=border_width
            )
            
            # Applica blur al layer glass (simulato con alpha)
            img = Image.alpha_composite(img.convert('RGBA'), glass_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Carica i font
            font_path = os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf')
            try:
                if os.path.exists(font_path):
                    header_font = ImageFont.truetype(font_path, 100)
                    message_font = ImageFont.truetype(font_path, 72)
                    footer_font = ImageFont.truetype(font_path, 40)
                else:
                    raise FileNotFoundError
            except:
                # Font di sistema
                try:
                    header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
                    message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 72)
                    footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                except:
                    # Fallback
                    try:
                        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
                        message_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
                        footer_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
                    except:
                        header_font = ImageFont.load_default()
                        message_font = ImageFont.load_default()
                        footer_font = ImageFont.load_default()
            
            # Disegna "SPOTTED" header con effetto glow
            header_text = "SPOTTED"
            header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
            header_width = header_bbox[2] - header_bbox[0]
            header_height = header_bbox[3] - header_bbox[1]
            header_x = (width - header_width) // 2
            header_y = 200
            
            # Effetto glow (ombra multipla)
            for offset_x, offset_y, opacity in [(0, 0, 200), (2, 2, 100), (4, 4, 50)]:
                draw.text(
                    (header_x + offset_x, header_y + offset_y),
                    header_text,
                    fill=(255, 255, 255, opacity),
                    font=header_font
                )
            
            # Testo principale
            draw.text((header_x, header_y), header_text, fill='#ffffff', font=header_font)
            
            # Disegna il messaggio con word wrap professionale
            message_y = 400
            max_width = width - (padding * 2)
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 110  # Spaziatura tra righe
            
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
            
            # Disegna le righe del messaggio centrate
            for i, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_y + i * line_height
                
                # Ombra leggera per leggibilità
                draw.text((line_x + 2, y_pos + 2), line, fill='#000000', font=message_font)
                # Testo principale
                draw.text((line_x, y_pos), line, fill='#e0e0e0', font=message_font)
            
            # Disegna footer "@spottedatbz"
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = height - 150
            
            # Footer con opacità
            draw.text((footer_x, footer_y), footer_text, fill='#ffffff', font=footer_font)
            
            # Aggiungi glow effect al bordo (simulato con linee)
            glow_color = (52, 89, 235)  # Blu glow
            for i in range(3):
                alpha = 30 - (i * 10)
                draw.rectangle(
                    [padding - i, padding - i, width - padding + i, height - padding + i],
                    outline=(glow_color[0], glow_color[1], glow_color[2], alpha),
                    width=1
                )
            
            # Salva l'immagine con alta qualità
            img.save(output_path, 'PNG', quality=100, optimize=True)
            print(f"✅ Immagine generata con PIL (design professionale): {output_path}")
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