import imgkit
import jinja2
import os
from pathlib import Path
from config import settings

# Import PIL come fallback di emergenza per problemi di compatibilità wkhtmltoimage
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

    def _render_html(self, message_text: str, message_id: int) -> str:
        """Carica il template HTML e inserisce il messaggio e l'URL del font."""
        template = self.template_env.get_template(os.path.basename(settings.image.template_path))

        # Crea un URL assoluto e corretto per il file del font
        font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
        font_url = Path(font_path).as_uri()

        return template.render(message=message_text, id=message_id, font_url=font_url)

    def _generate_with_pil(self, message_text: str, output_path: str, message_id: int) -> str | None:
        """Fallback di emergenza: genera un'immagine PIL con stile Apple quando wkhtmltoimage fallisce."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL non disponibile")

        try:
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920
            padding = 90

            # === SFONDO NERO CON GLOWS DELICATI ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)

            # Gradiente nero sottile
            for y in range(height):
                t = y / height
                r = int(0 + 2 * t)
                g = int(0 + 2 * t)
                b = int(0 + 2 * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Glows radiali delicati
            ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            amb_draw = ImageDraw.Draw(ambient)

            # Glow blu centrale
            for radius, alpha in [(500, 30), (350, 18), (200, 10)]:
                amb_draw.ellipse(
                    [width//2 - radius, height//2 - radius,
                     width//2 + radius, height//2 + radius],
                    fill=(0, 122, 255, alpha)
                )

            # Glow azzurro laterale
            for radius, alpha in [(300, 15), (180, 8)]:
                amb_draw.ellipse(
                    [int(width*0.3) - radius, int(height*0.4) - radius,
                     int(width*0.3) + radius, int(height*0.4) + radius],
                    fill=(90, 200, 250, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), ambient).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === CARD GLASSMORPHISM ===
            card_x = padding
            card_y = padding
            card_w = width - (padding * 2)
            card_h = height - (padding * 2)

            # Ombra morbida
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            for i in range(18):
                alpha = int(55 - i * 2.8)
                shadow_draw.rectangle(
                    [card_x + i + 6, card_y + i + 6,
                     card_x + card_w + i + 6, card_y + card_h + i + 6],
                    fill=(0, 0, 0, alpha)
                )
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Glow blu sottile
            glow_outer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_outer_draw = ImageDraw.Draw(glow_outer)
            for i in range(10):
                off = i * 2.5
                alpha = int(45 - i * 4)
                glow_outer_draw.rectangle(
                    [card_x - off, card_y - off,
                     card_x + card_w + off, card_y + card_h + off],
                    outline=(0, 122, 255, alpha)
                )
            img = Image.alpha_composite(img.convert('RGBA'), glow_outer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale glassmorphism
            draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(20, 20, 20, 200),
                outline=(255, 255, 255, 20)
            )

            # Highlight superiore
            for i in range(350):
                alpha = max(0, 70 - int(i * 0.2))
                draw.line(
                    [(card_x, card_y + i), (card_x + card_w, card_y + i)],
                    fill=(255, 255, 255, alpha)
                )

            # === CARICA FONT KOMIKA AXIS ===
            font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))

            brand_font = None
            message_font = None
            id_font = None
            footer_font = None

            if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
                try:
                    brand_font = ImageFont.truetype(font_path, 95)
                    message_font = ImageFont.truetype(font_path, 62)
                    id_font = ImageFont.truetype(font_path, 26)
                    footer_font = ImageFont.truetype(font_path, 30)
                except Exception as e:
                    print(f"⚠️ Errore nel caricamento font Komika Axis: {e}")

            if not brand_font:
                try:
                    if os.name == 'nt':
                        try:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 95)
                        except:
                            brand_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 95)
                        message_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 62)
                        id_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
                        footer_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
                    else:
                        brand_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95)
                        message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 62)
                        id_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
                        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
                except:
                    brand_font = ImageFont.load_default()
                    message_font = ImageFont.load_default()
                    id_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()

            # === BRAND "SPOTTED" ===
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 150

            # Ombra leggera
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.text((brand_x + 2, brand_y + 2), brand_text, fill=(0, 122, 255, 25), font=brand_font)
            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            draw.text((brand_x, brand_y), brand_text, fill='#ffffff', font=brand_font)

            # === BADGE ID ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + 120

            badge = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)
            pad_x, pad_y = 30, 12
            bdraw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + 32 + pad_y],
                radius=25,
                fill=(0, 122, 255, 30),
                outline=(0, 122, 255, 60)
            )
            img = Image.alpha_composite(img.convert('RGBA'), badge).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#5ac8fa', font=id_font)

            # === MESSAGGIO ===
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            max_width = card_w - 200
            line_height = 93

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

            message_start_y = id_y + 140

            for i, line in enumerate(lines[:3]):  # Max 3 righe
                if not line.strip():
                    continue

                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height

                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.text((line_x + 1, y_pos + 1), line, fill=(0, 0, 0, 45), font=message_font)
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)

                draw.text((line_x, y_pos), line, fill='#ffffff', font=message_font)

            # === FOOTER ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 200

            draw.text((footer_x, footer_y), footer_text, fill=(140, 140, 140), font=footer_font)

            # Salva con qualità massima
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata con successo (PIL fallback): {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Errore PIL fallback: {e}")
            raise

    def from_text(self, message_text: str, output_filename: str, message_id: int) -> str | None:
        """
        Genera un'immagine PNG da un testo utilizzando wkhtmltoimage con template HTML (preferenziale)
        o PIL come fallback di emergenza per problemi di compatibilità.

        Args:
            message_text: Il testo da inserire nell'immagine.
            output_filename: Il nome del file di output (es. 'spotted_123.png').
            message_id: L'ID del messaggio, da passare al template.

        Returns:
            Il percorso del file generato, o None se si verifica un errore.
        """
        # Definisce il percorso completo per il file di output
        output_path = os.path.join(self.output_folder, output_filename)

        # Prima prova con wkhtmltoimage (metodo preferenziale)
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

                # Genera l'immagine dall'HTML usando wkhtmltoimage
                imgkit.from_string(html_content, output_path, options=options, config=self.config)

                print(f"Immagine generata con successo (wkhtmltoimage): {output_path}")
                return output_path

            except Exception as e:
                # Controlla se è un errore di compatibilità GLIBC o librerie
                error_str = str(e).lower()
                is_glibc_error = ('glibc' in error_str and ('version' in error_str or 'not found' in error_str)) or \
                                'exited with non-zero code' in error_str

                if is_glibc_error:
                    print(f"⚠️ wkhtmltoimage ha problemi di compatibilità GLIBC, provo con PIL come fallback...")
                else:
                    print(f"⚠️ Errore con wkhtmltoimage: {e}")
                    print("Provo con PIL come fallback...")

                # Se wkhtmltoimage fallisce, prova PIL come fallback di emergenza
                if PIL_AVAILABLE:
                    try:
                        return self._generate_with_pil(message_text, output_path, message_id)
                    except Exception as pil_error:
                        print(f"❌ Anche PIL ha fallito: {pil_error}")
                        raise RuntimeError(f"Entrambi i metodi di generazione immagini hanno fallito. HTML error: {e}, PIL error: {pil_error}") from pil_error
                else:
                    raise RuntimeError(f"wkhtmltoimage fallito e PIL non disponibile: {e}") from e
        else:
            # wkhtmltoimage non disponibile, usa direttamente PIL come fallback
            print("⚠ wkhtmltoimage non disponibile, uso PIL come fallback...")
            if PIL_AVAILABLE:
                try:
                    return self._generate_with_pil(message_text, output_path, message_id)
                except Exception as pil_error:
                    raise RuntimeError(f"PIL fallback fallito: {pil_error}") from pil_error
            else:
                raise RuntimeError("ERRORE CRITICO: né wkhtmltoimage né PIL sono disponibili per generare immagini.")

# Esempio di utilizzo (per testare questo file singolarmente)
if __name__ == '__main__':
    generator = ImageGenerator()
    test_message = "Ho spottato una ragazza con un libro di poesie alla fermata del 17. Mi ha sorriso e ha reso la mia giornata migliore. Chissà se leggerà mai questo messaggio."

    # Genera l'immagine
    image_path = generator.from_text(test_message, "test_card.png", 1)

    if image_path:
        print(f"\nTest completato. Immagine di prova creata in: {image_path}")
        print("Aprila per vedere il risultato!")
