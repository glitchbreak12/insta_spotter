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
        """Genera un'immagine con stile azzurro/blu, 3D, liquid glass glow e ottimizzazione spazio."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            import math
            
            # Percorso root del progetto
            project_root = Path(__file__).parent.parent.parent
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 60
            
            # === SFONDO SEMPLICE AZZURRO/BLU ===
            img = Image.new('RGB', (width, height), color='#0a1628')
            draw = ImageDraw.Draw(img)
            
            # Gradiente azzurro/blu semplice
            for y in range(height):
                progress = y / height
                # Gradiente: blu scuro -> azzurro -> blu
                if progress < 0.5:
                    # Top: blu scuro -> azzurro
                    r = int(10 + (40 * progress * 2))
                    g = int(22 + (100 * progress * 2))
                    b = int(40 + (160 * progress * 2))
                else:
                    # Bottom: azzurro -> blu scuro
                    local = (progress - 0.5) * 2
                    r = int(50 - (40 * local))
                    g = int(122 - (100 * local))
                    b = int(200 - (160 * local))
                
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # === CARD 3D CON OMBRA PRONUNCIATA ===
            card_x = padding
            card_y = padding + 40
            card_w = width - (padding * 2)
            card_h = height - (padding * 2) - 80
            
            # Ombra 3D grande e pronunciata (prima della card)
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            # Ombra 3D con blur effect
            for i in range(30):
                alpha = int(80 - (i * 2.5))
                shadow_draw.rectangle(
                    [card_x + i + 20, card_y + i + 20,
                     card_x + card_w + i + 20, card_y + card_h + i + 20],
                    fill=(0, 0, 0, alpha)
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === GLOW ESTERNO AZZURRO PER 3D ===
            glow_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_card)
            
            # Glow azzurro attorno alla card per effetto 3D
            for i in range(25):
                offset = i * 1.5
                glow_alpha = int(180 - (i * 6))
                glow_draw.rectangle(
                    [card_x - offset, card_y - offset,
                     card_x + card_w + offset, card_y + card_h + offset],
                    outline=(100, 200, 255, glow_alpha),  # Azzurro glow
                    width=3
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), glow_card).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === LIQUID GLASS CARD PRONUNCIATO ===
            glass_card = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glass_draw = ImageDraw.Draw(glass_card)
            
            # Bordo esterno glow bianco (liquid glass)
            for i in range(25):
                alpha = int(60 + (i * 4))
                glass_draw.rectangle(
                    [card_x - i, card_y - i,
                     card_x + card_w + i, card_y + card_h + i],
                    outline=(255, 255, 255, alpha),
                    width=2
                )
            
            # Sfondo glass principale (liquid glass molto trasparente)
            glass_draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(15, 35, 65, 100),  # Blu scuro molto trasparente per liquid glass
                outline=(200, 230, 255, 150),  # Bordo azzurro brillante
                width=3
            )
            
            # Highlight superiore pronunciato (riflesso liquid glass)
            highlight_y = card_y + 50
            for i in range(80):
                alpha = int(150 - (i * 1.8))
                glass_draw.rectangle(
                    [card_x + 50, highlight_y + i,
                     card_x + card_w - 50, highlight_y + i + 1],
                    fill=(255, 255, 255, alpha)
                )
            
            # Bordo interno glow azzurro intenso
            for i in range(15):
                alpha = int(150 - (i * 10))
                glass_draw.rectangle(
                    [card_x + 20 + i, card_y + 20 + i,
                     card_x + card_w - 20 - i, card_y + card_h - 20 - i],
                    outline=(100, 200, 255, alpha),  # Azzurro glow intenso
                    width=2
                )
            
            # Glow interno aggiuntivo per liquid glass
            for i in range(8):
                alpha = int(80 - (i * 10))
                glass_draw.rectangle(
                    [card_x + 35 + i, card_y + 35 + i,
                     card_x + card_w - 35 - i, card_y + card_h - 35 - i],
                    outline=(150, 220, 255, alpha),  # Azzurro glow chiaro
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
            
            # === BRANDING "SPOTTED" CON GLOW AZZURRO INTENSO 3D ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_height = brand_bbox[3] - brand_bbox[1]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 100
            
            # Glow azzurro intenso multiplo per "SPOTTED" (3D effect)
            for i in range(20):
                offset = i * 2.5
                alpha = int(220 - (i * 10))
                # Glow in tutte le direzioni per effetto 3D
                for dx, dy in [(offset, offset), (-offset, offset), (offset, -offset), (-offset, -offset),
                               (offset, 0), (-offset, 0), (0, offset), (0, -offset),
                               (offset*0.7, offset*0.7), (-offset*0.7, offset*0.7)]:
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (brand_x + int(dx), brand_y + int(dy)),
                        brand_text,
                        fill=(100, 200, 255, alpha),  # Azzurro glow intenso
                        font=brand_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
            
            # Ombre multiple per 3D pronunciato
            for offset in [(6, 6), (4, 4), (2, 2)]:
                draw.text(
                    (brand_x + offset[0], brand_y + offset[1]),
                    brand_text,
                    fill='#000000',
                    font=brand_font
                )
            
            # Testo principale azzurro brillante
            draw.text((brand_x, brand_y), brand_text, fill='#64b5f6', font=brand_font)
            
            # === ID POST "sp#ID" ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + brand_height + 50
            
            draw.text((id_x, id_y), id_text, fill='#90caf9', font=id_font)
            
            # === MESSAGGIO CON WORD WRAP OTTIMIZZATO ===
            # Ottimizzazione spazio: calcola area disponibile
            message_area_top = id_y + 70
            message_area_bottom = card_y + card_h - 100  # Spazio ottimizzato per footer
            message_area_height = message_area_bottom - message_area_top
            
            max_width = card_w - 120  # Padding ottimizzato
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 90  # Ottimizzato per spazio
            
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
            
            # Calcola altezza totale e centra verticalmente
            total_message_height = len(lines) * line_height
            message_start_y = message_area_top + max(0, (message_area_height - total_message_height) // 2)
            
            # Disegna messaggio con glow azzurro
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height
                
                # Glow azzurro intenso per messaggio (3D)
                for glow_i in range(8):
                    offset = glow_i * 1.5
                    alpha = int(120 - (glow_i * 14))
                    # Glow in più direzioni
                    for dx, dy in [(offset, offset), (offset, 0), (0, offset)]:
                        glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                        glow_draw = ImageDraw.Draw(glow_layer)
                        glow_draw.text(
                            (line_x + int(dx), y_pos + int(dy)),
                            line,
                            fill=(150, 220, 255, alpha),  # Azzurro glow intenso
                            font=message_font
                        )
                        img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                        draw = ImageDraw.Draw(img)
                
                # Ombre multiple per 3D pronunciato
                for offset in [(4, 4), (2, 2)]:
                    draw.text((line_x + offset[0], y_pos + offset[1]), line, fill='#000000', font=message_font)
                # Testo principale bianco brillante
                draw.text((line_x, y_pos), line, fill='#ffffff', font=message_font)
            
            # === FOOTER "@spottedatbz" CON GLOW ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 90
            
            # Glow azzurro intenso per footer (3D)
            for glow_i in range(8):
                offset = glow_i * 1.2
                alpha = int(140 - (glow_i * 17))
                # Glow in più direzioni
                for dx, dy in [(offset, offset), (offset, 0), (0, offset)]:
                    glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)
                    glow_draw.text(
                        (footer_x + int(dx), footer_y + int(dy)),
                        footer_text,
                        fill=(100, 200, 255, alpha),  # Azzurro glow intenso
                        font=footer_font
                    )
                    img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)
            
            # Ombre per 3D
            for offset in [(3, 3), (1, 1)]:
                draw.text((footer_x + offset[0], footer_y + offset[1]), footer_text, fill='#000000', font=footer_font)
            # Footer azzurro brillante
            draw.text((footer_x, footer_y), footer_text, fill='#90caf9', font=footer_font)
            
            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata (stile azzurro/blu, 3D, liquid glass glow): {output_path}")
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