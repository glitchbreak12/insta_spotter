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
        """Genera un'immagine con stile luxury futuristic neon, glow azzurro, liquid glass Apple 3D."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            import math
            
            # Percorso root del progetto
            project_root = Path(__file__).parent.parent.parent
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 80
            
            # === SFONDO CON GLOWING GRADIENT ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)
            
            # Gradiente complesso con glow blu/viola
            for y in range(height):
                progress = y / height
                
                # Gradiente: nero -> blu scuro -> viola -> blu
                if progress < 0.25:
                    # Top: nero -> blu scuro
                    r = int(0 + (20 * progress * 4))
                    g = int(0 + (30 * progress * 4))
                    b = int(0 + (60 * progress * 4))
                elif progress < 0.5:
                    # Middle-top: blu scuro -> viola
                    local = (progress - 0.25) * 4
                    r = int(20 + (40 * local))
                    g = int(30 + (20 * local))
                    b = int(60 + (30 * local))
                elif progress < 0.75:
                    # Middle-bottom: viola -> blu brillante
                    local = (progress - 0.5) * 4
                    r = int(60 - (20 * local))
                    g = int(50 - (10 * local))
                    b = int(90 + (40 * local))
                else:
                    # Bottom: blu brillante -> blu scuro
                    local = (progress - 0.75) * 4
                    r = int(40 - (20 * local))
                    g = int(40 - (10 * local))
                    b = int(130 - (50 * local))
                
                # Aggiungi glow dinamico
                glow = math.sin(progress * math.pi * 6) * 15
                r = max(0, min(255, int(r + glow)))
                g = max(0, min(255, int(g + glow)))
                b = max(0, min(255, int(b + glow)))
                
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # === GLOWING BACKGROUND EFFECTS ===
            glow_bg = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_bg_draw = ImageDraw.Draw(glow_bg)
            
            # Glow radiali multipli (simulati)
            center_x, center_y = width // 2, height // 2
            for i in range(3):
                radius = 300 + (i * 200)
                alpha = int(80 - (i * 20))
                # Glow blu
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    x = int(center_x + radius * math.cos(rad))
                    y = int(center_y + radius * math.sin(rad))
                    if 0 <= x < width and 0 <= y < height:
                        glow_bg_draw.ellipse(
                            [x - 50, y - 50, x + 50, y + 50],
                            fill=(59, 130, 246, alpha)
                        )
            
            img = Image.alpha_composite(img.convert('RGBA'), glow_bg).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === LIQUID GLASS CARD 3D ===
            card_x = padding
            card_y = padding
            card_w = width - (padding * 2)
            card_h = height - (padding * 2)
            
            # Glow esterno intenso (3D effect)
            glow_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_card_draw = ImageDraw.Draw(glow_card)
            
            # Glow multipli per effetto 3D
            glow_colors = [
                (59, 130, 246, 120),   # Blu
                (139, 92, 246, 100),   # Viola
                (99, 102, 241, 80),    # Indigo
            ]
            
            for glow_idx, (gr, gg, gb, alpha) in enumerate(glow_colors):
                for i in range(25):
                    offset = i * 2
                    glow_alpha = int(alpha * (1 - i / 25))
                    glow_card_draw.rectangle(
                        [card_x - offset, card_y - offset,
                         card_x + card_w + offset, card_y + card_h + offset],
                        outline=(gr, gg, gb, glow_alpha),
                        width=3
                    )
            
            img = Image.alpha_composite(img.convert('RGBA'), glow_card).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === LIQUID GLASS CARD ===
            glass_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glass_draw = ImageDraw.Draw(glass_card)
            
            # Sfondo glass con blur effect (simulato con gradiente)
            # Bordo esterno glow
            for i in range(15):
                alpha = int(30 + (i * 2))
                glass_draw.rectangle(
                    [card_x - i, card_y - i,
                     card_x + card_w + i, card_y + card_h + i],
                    outline=(255, 255, 255, alpha),
                    width=1
                )
            
            # Sfondo glass principale (liquid glass)
            glass_draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(30, 41, 59, 100),  # Semi-trasparente
                outline=(255, 255, 255, 60),
                width=3
            )
            
            # Highlight superiore (riflesso glass)
            highlight_y = card_y + 30
            for i in range(40):
                alpha = int(100 - (i * 2))
                glass_draw.rectangle(
                    [card_x + 30, highlight_y + i,
                     card_x + card_w - 30, highlight_y + i + 2],
                    fill=(255, 255, 255, alpha)
                )
            
            # Bordo interno glow
            for i in range(8):
                alpha = int(120 - (i * 15))
                glass_draw.rectangle(
                    [card_x + 10 + i, card_y + 10 + i,
                     card_x + card_w - 10 - i, card_y + card_h - 10 - i],
                    outline=(59, 130, 246, alpha),
                    width=1
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), glass_card).convert('RGB')
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
            
            # === BRANDING "SPOTTED" CON NEON GLOW LUXURY ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_height = brand_bbox[3] - brand_bbox[1]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 100
            
            # Glow neon azzurro multiplo (stile luxury futuristic)
            for i in range(15):
                offset = i * 2.5
                alpha = int(200 - (i * 12))
                # Glow azzurro neon in tutte le direzioni
                for dx, dy in [(offset, offset), (-offset, offset), (offset, -offset), (-offset, -offset),
                               (offset, 0), (-offset, 0), (0, offset), (0, -offset),
                               (offset*0.7, offset*0.7), (-offset*0.7, offset*0.7)]:
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (brand_x + int(dx), brand_y + int(dy)),
                        brand_text,
                        fill=(100, 200, 255, alpha),  # Azzurro neon
                        font=brand_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
            
            # Ombra nera profonda per 3D luxury
            for offset in [(4, 4), (2, 2)]:
                draw.text(
                    (brand_x + offset[0], brand_y + offset[1]),
                    brand_text,
                    fill='#000000',
                    font=brand_font
                )
            
            # Testo principale azzurro neon brillante
            draw.text((brand_x, brand_y), brand_text, fill='#64d9ff', font=brand_font)
            
            # === ID POST "sp#ID" (opzionale, più piccolo) ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + brand_height + 40
            
            draw.text((id_x, id_y), id_text, fill='#cbd5e1', font=id_font)
            
            # === MESSAGGIO CON WORD WRAP (centrato verticalmente) ===
            # Calcola l'area disponibile per il messaggio
            message_area_top = id_y + 80
            message_area_bottom = card_y + card_h - 120  # Lascia spazio per footer
            message_area_height = message_area_bottom - message_area_top
            
            max_width = card_w - (padding * 2)
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 96  # 64px * 1.5 (line-height del template)
            
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
            
            # Calcola l'altezza totale del messaggio
            total_message_height = len(lines) * line_height
            
            # Centra verticalmente il messaggio nell'area disponibile
            message_start_y = message_area_top + (message_area_height - total_message_height) // 2
            
            # Disegna messaggio con neon glow luxury
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height
                
                # Glow azzurro neon per il messaggio
                for glow_i in range(6):
                    offset = glow_i * 1.5
                    alpha = int(120 - (glow_i * 18))
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (line_x + int(offset), y_pos + int(offset)),
                        line,
                        fill=(150, 220, 255, alpha),  # Azzurro neon chiaro
                        font=message_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
                
                # Ombra nera per profondità luxury
                draw.text((line_x + 2, y_pos + 2), line, fill='#000000', font=message_font)
                # Testo principale bianco luxury
                draw.text((line_x, y_pos), line, fill='#f0f9ff', font=message_font)
            
            # === FOOTER "@spottedatbz" CON NEON GLOW BRANDING ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 120
            
            # Glow azzurro neon per footer branding
            for glow_i in range(5):
                offset = glow_i * 1
                alpha = int(100 - (glow_i * 20))
                glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)
                glow_draw.text(
                    (footer_x + offset, footer_y + offset),
                    footer_text,
                    fill=(100, 200, 255, alpha),  # Azzurro neon
                    font=footer_font
                )
                img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)
            
            # Ombra
            draw.text((footer_x + 1, footer_y + 1), footer_text, fill='#000000', font=footer_font)
            # Footer azzurro neon luxury
            draw.text((footer_x, footer_y), footer_text, fill='#64d9ff', font=footer_font)
            
            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata (stile luxury futuristic neon, glow azzurro, liquid glass Apple 3D): {output_path}")
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