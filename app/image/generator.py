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
        """Genera un'immagine con stile originale semplice."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            # Percorso root del progetto
            project_root = Path(__file__).parent.parent.parent
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 80
            
            # === SFONDO LUXURY 3D ===
            img = Image.new('RGB', (width, height), color='#060a14')
            draw = ImageDraw.Draw(img)
            # gradiente verticale profondo
            for y in range(height):
                t = y / height
                r = int(8 + 18 * t)
                g = int(15 + 55 * t)
                b = int(26 + 120 * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            # glows ambientali
            ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            amb_draw = ImageDraw.Draw(ambient)
            for radius, alpha in [(520, 120), (380, 90), (260, 70)]:
                amb_draw.ellipse(
                    [width//2 - radius, height//2 - radius,
                     width//2 + radius, height//2 + radius],
                    fill=(80, 170, 255, alpha)
                )
            for radius, alpha in [(360, 80), (240, 60)]:
                amb_draw.ellipse(
                    [int(width*0.25) - radius, int(height*0.28) - radius,
                     int(width*0.25) + radius, int(height*0.28) + radius],
                    fill=(50, 110, 255, alpha)
                )
            img = Image.alpha_composite(img.convert('RGBA'), ambient).convert('RGB')
            draw = ImageDraw.Draw(img)
            # vignetta soft
            vignette = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            vig_draw = ImageDraw.Draw(vignette)
            max_r = int((width + height) * 0.65)
            cx, cy = width//2, height//2
            for i in range(max_r, 0, -10):
                alpha = int(110 * (1 - i / max_r))
                vig_draw.ellipse([cx - i, cy - i, cx + i, cy + i], outline=(0, 0, 0, alpha), width=8)
            img = Image.alpha_composite(img.convert('RGBA'), vignette).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === COORDINATE CARD ===
            card_x = padding
            card_y = padding
            card_w = width - (padding * 2)
            card_h = height - (padding * 2)

            # Ombra 3D pronunciata
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            for i in range(22):
                alpha = int(68 - i * 2.5)
                shadow_draw.rectangle(
                    [card_x + i + 16, card_y + i + 16,
                     card_x + card_w + i + 16, card_y + card_h + i + 16],
                    fill=(0, 0, 0, alpha)
                )
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card glass + glow multi-layer
            card_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_layer)
            card_draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(16, 24, 40, 230),
                outline=(140, 200, 255, 160),
                width=3
            )
            # highlight diagonale
            for i in range(0, card_h, 7):
                alpha = max(0, 70 - int(i * 0.05))
                card_draw.line(
                    [(card_x + 40, card_y + i), (card_x + card_w - 40, card_y + i + 90)],
                    fill=(255, 255, 255, alpha),
                    width=2
                )
            img = Image.alpha_composite(img.convert('RGBA'), card_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Glow bordo
            glow_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_card)
            for i in range(20):
                off = i * 1.4
                alpha = int(170 - i * 7)
                glow_draw.rectangle(
                    [card_x - off, card_y - off, card_x + card_w + off, card_y + card_h + off],
                    outline=(90, 185, 255, alpha),
                    width=3
                )
            img = Image.alpha_composite(img.convert('RGBA'), glow_card).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === CARICA FONT KOMIKA AXIS ===
            font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
            
            brand_font = None
            message_font = None
            id_font = None
            footer_font = None
            
            # Prova a caricare Komika Axis (verifica che non sia un placeholder)
            if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
                try:
                    brand_font = ImageFont.truetype(font_path, 80)  # Come nel template HTML
                    message_font = ImageFont.truetype(font_path, 64)  # Come nel template HTML
                    id_font = ImageFont.truetype(font_path, 32)
                    footer_font = ImageFont.truetype(font_path, 32)  # Come nel template HTML
                except Exception as e:
                    print(f"⚠️ Errore nel caricamento font Komika Axis: {e}")
            
            # Se Komika Axis non disponibile, usa font di sistema
            if not brand_font:
                try:
                    if os.name == 'nt':  # Windows
                        # Prova Arial Bold per il branding
                        try:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 80)
                        except:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 80)
                        message_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 64)
                        id_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
                        footer_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
                    else:  # Linux/Mac
                        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
                        message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)
                        id_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                except:
                    # Ultimo fallback
                    brand_font = ImageFont.load_default()
                    message_font = ImageFont.load_default()
                    id_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()
            
            # === BRANDING "SPOTTED" ORIGINALE ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_height = brand_bbox[3] - brand_bbox[1]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 70
            
            # Glow brand
            for i in range(14):
                alpha = int(150 - i * 9)
                for dx, dy in [(0, 0), (2, 2), (-2, -2), (2, -2), (-2, 2)]:
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (brand_x + dx, brand_y + dy),
                        brand_text,
                        fill=(130, 210, 255, alpha),
                        font=brand_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
            draw.text((brand_x, brand_y), brand_text, fill='#b9e6ff', font=brand_font)
            
            # ID post
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + brand_height + 24
            badge = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)
            pad_x, pad_y = 24, 12
            bdraw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + (id_bbox[3]-id_bbox[1]) + pad_y],
                radius=30,
                fill=(100, 180, 255, 60),
                outline=(140, 200, 255, 140),
                width=2
            )
            img = Image.alpha_composite(img.convert('RGBA'), badge).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#cfe9ff', font=id_font)
            
            # === MESSAGGIO CON WORD WRAP (centrato verticalmente) ===
            message_area_top = id_y + 90
            message_area_bottom = card_y + card_h - 170
            message_area_height = message_area_bottom - message_area_top
            
            max_width = card_w - (padding * 2)
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 96  # 64px * 1.5
            
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
            
            total_message_height = len(lines) * line_height
            message_start_y = message_area_top + (message_area_height - total_message_height) // 2
            
            # Messaggio con leggero glow
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height
                
                for g in range(4):
                    alpha = int(100 - g * 20)
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (line_x, y_pos),
                        line,
                        fill=(140, 220, 255, alpha),
                        font=message_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
                draw.text((line_x, y_pos), line, fill='#edf2f7', font=message_font)
            
            # === FOOTER "@spottedatbz" con glow leggero ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 90
            
            for g in range(3):
                alpha = int(80 - g * 22)
                glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)
                glow_draw.text(
                    (footer_x, footer_y),
                    footer_text,
                    fill=(120, 190, 255, alpha),
                    font=footer_font
                )
                img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)
            draw.text((footer_x, footer_y), footer_text, fill='#94a3b8', font=footer_font)
            
            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata (stile 3D glow luxury): {output_path}")
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