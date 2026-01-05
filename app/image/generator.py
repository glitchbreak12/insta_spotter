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
        """Genera un'immagine con design stile Apple - minimalista e pulito."""
        if not PIL_AVAILABLE:
            return False
        
        try:
            import math
            
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 80
            
            # === SFONDO STILE APPLE - Nero con glows delicati ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)
            
            # Gradiente nero molto sottile
            for y in range(height):
                t = y / height
                # Gradiente: nero puro -> nero leggermente più chiaro
                r = int(0 + 2 * t)
                g = int(0 + 2 * t)
                b = int(0 + 2 * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Glows radiali delicati stile Apple
            ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            amb_draw = ImageDraw.Draw(ambient)
            
            # Glow blu centrale delicato
            for radius, alpha in [(500, 40), (350, 25), (200, 15)]:
                amb_draw.ellipse(
                    [width//2 - radius, height//2 - radius,
                     width//2 + radius, height//2 + radius],
                    fill=(0, 122, 255, alpha)  # Blue Apple
                )
            
            # Glow azzurro laterale sinistro
            for radius, alpha in [(300, 20), (180, 12)]:
                amb_draw.ellipse(
                    [int(width*0.3) - radius, int(height*0.4) - radius,
                     int(width*0.3) + radius, int(height*0.4) + radius],
                    fill=(90, 200, 250, alpha)  # Azzurro Apple
                )
            
            # Glow blu laterale destro
            for radius, alpha in [(300, 20), (180, 12)]:
                amb_draw.ellipse(
                    [int(width*0.7) - radius, int(height*0.6) - radius,
                     int(width*0.7) + radius, int(height*0.6) + radius],
                    fill=(88, 86, 214, alpha)  # Blu viola Apple
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), ambient).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === CARD STILE APPLE - Glassmorphism ===
            card_x = padding
            card_y = padding
            card_w = width - (padding * 2)
            card_h = height - (padding * 2)

            # Ombra morbida stile Apple
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            for i in range(20):
                alpha = int(60 - i * 2.8)
                shadow_draw.rectangle(
                    [card_x + i + 8, card_y + i + 8,
                     card_x + card_w + i + 8, card_y + card_h + i + 8],
                    fill=(0, 0, 0, alpha)
                )
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Glow blu sottile attorno alla card
            glow_outer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_outer_draw = ImageDraw.Draw(glow_outer)
            for i in range(12):
                off = i * 2
                alpha = int(50 - i * 3)
                glow_outer_draw.rectangle(
                    [card_x - off, card_y - off,
                     card_x + card_w + off, card_y + card_h + off],
                    outline=(0, 122, 255, alpha),
                    width=2
                )
            img = Image.alpha_composite(img.convert('RGBA'), glow_outer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale glassmorphism stile Apple
            card_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_layer)
            card_draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(18, 18, 18, 190),  # Nero trasparente stile Apple
                outline=(255, 255, 255, 25),  # Bordo bianco sottile
                width=1
            )
            
            # Highlight superiore delicato
            highlight_y = card_y
            for i in range(300):
                alpha = max(0, 80 - int(i * 0.25))
                card_draw.line(
                    [(card_x, highlight_y + i), (card_x + card_w, highlight_y + i)],
                    fill=(255, 255, 255, alpha),
                    width=1
                )
            
            img = Image.alpha_composite(img.convert('RGBA'), card_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # === CARICA FONT KOMIKA AXIS ===
            font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
            
            brand_font = None
            message_font = None
            id_font = None
            footer_font = None
            
            if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
                try:
                    brand_font = ImageFont.truetype(font_path, 100)  # Stile Apple - più raffinato
                    message_font = ImageFont.truetype(font_path, 64)  # Stile Apple - leggibile
                    id_font = ImageFont.truetype(font_path, 28)  # Stile Apple - discreto
                    footer_font = ImageFont.truetype(font_path, 32)  # Stile Apple - elegante
                except Exception as e:
                    print(f"⚠️ Errore nel caricamento font Komika Axis: {e}")
            
            if not brand_font:
                try:
                    if os.name == 'nt':
                        try:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 100)
                        except:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 100)
                        message_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 64)
                        id_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
                        footer_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
                    else:
                        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
                        message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)
                        id_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                except:
                    brand_font = ImageFont.load_default()
                    message_font = ImageFont.load_default()
                    id_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()
            
            # === BRAND "SPOTTED" STILE APPLE - Bianco con ombra leggera ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_height = brand_bbox[3] - brand_bbox[1]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 100  # Posizionamento corretto
            
            # Ombra leggera stile Apple
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.text((brand_x + 2, brand_y + 2), brand_text, fill=(0, 122, 255, 30), font=brand_font)
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Testo brand bianco stile Apple
            draw.text((brand_x, brand_y), brand_text, fill='#ffffff', font=brand_font)
            
            # === BADGE ID STILE APPLE - Pulito e minimale ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_height = id_bbox[3] - id_bbox[1]
            id_x = (width - id_width) // 2
            id_y = brand_y + brand_height + 50  # Spacing aumentato per evitare sovrapposizioni
            
            # Badge stile Apple - pulito
            badge = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)
            pad_x, pad_y = 24, 10
            bdraw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + id_height + pad_y],
                radius=20,
                fill=(0, 122, 255, 40),  # Blu Apple trasparente
                outline=(0, 122, 255, 80),  # Bordo blu Apple
                width=1
            )
            img = Image.alpha_composite(img.convert('RGBA'), badge).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#5ac8fa', font=id_font)  # Azzurro Apple
            
            # === MESSAGGIO STILE APPLE - Bianco pulito ===
            # Calcola l'altezza totale del badge incluso padding
            badge_total_height = id_height + (pad_y * 2)
            message_area_top = id_y + badge_total_height + 80  # Spacing aumentato
            message_area_bottom = card_y + card_h - 250  # Spazio footer aumentato
            message_area_height = message_area_bottom - message_area_top
            
            # Verifica che ci sia spazio sufficiente
            if message_area_height < 100:
                message_area_bottom = card_y + card_h - 200
                message_area_height = message_area_bottom - message_area_top
            
            max_width = card_w - (padding * 2) - 60
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            line_height = 102  # 64px * 1.6 (line-height Apple)
            
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
            
            # Verifica che il messaggio non sia troppo alto
            if total_message_height > message_area_height:
                # Riduci line_height se necessario
                line_height = max(80, message_area_height // len(lines))
                total_message_height = len(lines) * line_height
            
            message_start_y = message_area_top + max(0, (message_area_height - total_message_height) // 2)
            
            # Messaggio bianco stile Apple - senza glow eccessivo
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height
                
                # Verifica che non si sovrapponga al footer
                if y_pos + line_height > message_area_bottom:
                    break
                
                # Ombra leggera
                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.text((line_x + 1, y_pos + 1), line, fill=(0, 0, 0, 50), font=message_font)
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)
                
                # Testo bianco
                draw.text((line_x, y_pos), line, fill='#ffffff', font=message_font)
            
            # === FOOTER STILE APPLE - Grigio elegante ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_height = footer_bbox[3] - footer_bbox[1]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 150  # Posizionamento sicuro
            
            # Verifica che il footer non si sovrapponga al messaggio
            last_message_y = message_start_y + (len(lines) - 1) * line_height + line_height
            if footer_y < last_message_y + 50:
                footer_y = last_message_y + 80
            
            # Footer grigio stile Apple
            draw.text((footer_x, footer_y), footer_text, fill=(153, 153, 153), font=footer_font)  # Grigio 60% opacità
            
            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata (stile Apple - minimalista e pulito): {output_path}")
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