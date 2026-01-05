import imgkit
import jinja2
import os
from pathlib import Path
from config import settings

# Import PIL come fallback di emergenza per problemi di compatibilità wkhtmltoimage
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
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
        """Fallback PIL che replica esattamente lo stile card_v5.html con glow 3D."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL non disponibile")

        try:
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920

            # === SFONDO STILE APPLE ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)

            # Sfondo con gradiente sottile (come card_v5)
            for y in range(height):
                t = y / height
                r = int(0 + 2 * t)
                g = int(0 + 2 * t)
                b = int(0 + 2 * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Glows radiali come bg-container in card_v5
            ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            amb_draw = ImageDraw.Draw(ambient)

            # Glow centrale a 30% 40%
            for radius, alpha in [(400, 30), (250, 18)]:  # rgba(0, 122, 255, 0.12) ≈ 30/255
                amb_draw.ellipse(
                    [int(width*0.3) - radius, int(height*0.4) - radius,
                     int(width*0.3) + radius, int(height*0.4) + radius],
                    fill=(0, 122, 255, alpha)
                )

            # Glow laterale a 70% 60%
            for radius, alpha in [(400, 25), (250, 15)]:  # rgba(88, 86, 214, 0.1) ≈ 25/255
                amb_draw.ellipse(
                    [int(width*0.7) - radius, int(height*0.6) - radius,
                     int(width*0.7) + radius, int(height*0.6) + radius],
                    fill=(88, 86, 214, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), ambient).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === CARD CON GLOW 3D IDENTICO A card_v5.html ===
            card_x = 90  # padding: 90px come card_v5
            card_y = 90
            card_w = width - 180  # 1080 - (90*2)
            card_h = height - 180  # 1920 - (90*2)

            # Simula il ::before pseudo-element (glow radiale)
            before_glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            before_draw = ImageDraw.Draw(before_glow)

            # Glow radiale come ::before: top: -30%, left: -30%, width: 160%, height: 160%
            glow_center_x = card_x + card_w // 2
            glow_center_y = card_y + card_h // 2
            glow_radius = int(max(card_w, card_h) * 0.8)  # 160% / 2 ≈ 80%

            for radius in range(glow_radius, 0, -2):
                alpha = int(127 * (1 - radius/glow_radius) * 0.5)  # opacity: 0.5
                before_draw.ellipse(
                    [glow_center_x - radius, glow_center_y - radius,
                     glow_center_x + radius, glow_center_y + radius],
                    fill=(0, 122, 255, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), before_glow).convert('RGB')
            draw = ImageDraw.Draw(img)

            # BOX-SHADOW 3D esatto come card_v5 (4 livelli)
            shadow_3d = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_3d)

            # 1. Inner light glow: 0 0 10px rgba(0, 122, 255, 0.3)
            for i in range(5):
                alpha = int(77 - i * 15)  # 0.3 * 255 ≈ 77
                shadow_draw.rectangle(
                    [card_x - 10 + i, card_y - 10 + i,
                     card_x + card_w + 10 - i, card_y + card_h + 10 - i],
                    outline=(0, 122, 255, alpha)
                )

            # 2. Medium glow: 0 0 40px rgba(0, 122, 255, 0.2)
            for i in range(10):
                alpha = int(51 - i * 5)  # 0.2 * 255 ≈ 51
                shadow_draw.rectangle(
                    [card_x - 40 + i*4, card_y - 40 + i*4,
                     card_x + card_w + 40 - i*4, card_y + card_h + 40 - i*4],
                    outline=(0, 122, 255, alpha)
                )

            # 3. Outer subtle glow: 0 0 80px rgba(0, 122, 255, 0.15)
            for i in range(15):
                alpha = int(38 - i * 2.5)  # 0.15 * 255 ≈ 38
                shadow_draw.rectangle(
                    [card_x - 80 + i*5, card_y - 80 + i*5,
                     card_x + card_w + 80 - i*5, card_y + card_h + 80 - i*5],
                    outline=(0, 122, 255, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), shadow_3d).convert('RGB')
            draw = ImageDraw.Draw(img)

            # 4. Deep dark shadow: 0 20px 60px rgba(0, 0, 0, 0.7)
            deep_shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            deep_draw = ImageDraw.Draw(deep_shadow)

            for i in range(25):
                alpha = int(179 - i * 7)  # 0.7 * 255 ≈ 179
                offset_x = i * 2  # Simula blur
                offset_y = 20 + i  # 20px offset
                deep_draw.rectangle(
                    [card_x + offset_x, card_y + offset_y,
                     card_x + card_w - offset_x, card_y + card_h + offset_y],
                    fill=(0, 0, 0, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), deep_shadow).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale con backdrop-filter simulato (blur + saturate)
            card_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_layer)

            # Simula backdrop-filter: blur(55px) saturate(190%)
            # Crea una versione molto sfocata per simulare il blur
            blur_bg = img.filter(ImageFilter.GaussianBlur(radius=8))  # blur(55px) ≈ radius 8

            # Applica saturazione extra (saturate(190%))
            # PIL non ha saturate diretto, simuliamo con un filtro di contrasto
            enhancer = ImageEnhance.Contrast(blur_bg)
            blur_bg = enhancer.enhance(1.9)  # 190% contrast ≈ saturation boost

            # Maschera per la card
            mask = Image.new('L', (card_w, card_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([0, 0, card_w, card_h], radius=45, fill=255)

            # Applica la maschera sfocata alla card
            card_region = blur_bg.crop((card_x, card_y, card_x + card_w, card_y + card_h))
            card_layer.paste(card_region, (card_x, card_y), mask)

            # Overlay semi-trasparente come rgba(20, 20, 20, 0.8)
            overlay = Image.new('RGBA', (width, height), (20, 20, 20, 204))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                fill=(20, 20, 20, 204)
            )

            # Bordo sottile come border: 1px solid rgba(255,255,255,0.08)
            border_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(border_layer)
            border_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                outline=(255, 255, 255, 20),
                width=2  # Simula 1px border
            )

            img = Image.alpha_composite(img.convert('RGBA'), card_layer).convert('RGB')
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            img = Image.alpha_composite(img.convert('RGBA'), border_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Highlight superiore esatto come card_v5
            highlight_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            highlight_draw = ImageDraw.Draw(highlight_layer)

            for y in range(350):  # height: 350px
                # linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, transparent 100%)
                alpha = max(0, int(15 * (1 - y/350)))  # 0.06 * 255 ≈ 15
                highlight_draw.line(
                    [(card_x, card_y + y), (card_x + card_w, card_y + y)],
                    fill=(255, 255, 255, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), highlight_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === CARICA FONT KOMIKA AXIS ===
            font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))

            brand_font = None
            message_font = None
            id_font = None
            footer_font = None

            if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
                try:
                    brand_font = ImageFont.truetype(font_path, 95)  # font-size: 95px come card_v5
                    message_font = ImageFont.truetype(font_path, 62)  # font-size: 62px come card_v5
                    id_font = ImageFont.truetype(font_path, 26)  # font-size: 26px come card_v5
                    footer_font = ImageFont.truetype(font_path, 30)  # font-size: 30px come card_v5
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

            # === HEADER CON BRAND E BADGE ===
            header_y = card_y + 50  # padding-top: 50px come card_v5

            # BRAND "SPOTTED" con text-shadow 3D esatto come card_v5
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = header_y

            # Text shadows esatti come card_v5 (4 livelli)
            for dx, dy, color, alpha in [
                (0, 0, (0, 122, 255), 128),  # 0 0 10px rgba(0,122,255,0.5) ≈ 128/255
                (0, 0, (0, 122, 255), 77),   # 0 0 20px rgba(0,122,255,0.3) ≈ 77/255
                (0, 0, (0, 122, 255), 25),   # 0 0 30px rgba(0,122,255,0.1) ≈ 25/255
                (0, 2, (0, 0, 0), 204)       # 0 2px 5px rgba(0,0,0,0.8) ≈ 204/255
            ]:
                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.text((brand_x + dx, brand_y + dy), brand_text, fill=color + (alpha,), font=brand_font)
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)

            draw.text((brand_x, brand_y), brand_text, fill='#ffffff', font=brand_font)

            # BADGE ID come card_v5
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + 95 + 35  # margin-bottom: 35px come card_v5

            badge = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)
            pad_x, pad_y = 30, 12  # padding: 12px 30px come card_v5
            bdraw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + 32 + pad_y],
                radius=25,  # border-radius: 25px come card_v5
                fill=(0, 122, 255, 30),  # rgba(0,122,255,0.12) ≈ 30/255
                outline=(0, 122, 255, 64)  # rgba(0,122,255,0.25) ≈ 64/255
            )
            img = Image.alpha_composite(img.convert('RGBA'), badge).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#5ac8fa', font=id_font)  # color: #5ac8fa come card_v5

            # === BODY CON MESSAGGIO ===
            body_top = id_y + 80  # margin-bottom: 80px dell'header
            body_bottom = card_y + card_h - 100  # Prima del footer

            # Word wrap per max-width: 80% come card_v5
            words = message_text.split()
            lines = []
            current_line = []
            current_width = 0
            max_width = int(card_w * 0.8)  # max-width: 80%
            line_height = int(62 * 1.5)  # line-height: 1.5

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

            # Centro verticale nel body (flexbox center)
            total_message_height = len(lines) * line_height
            message_start_y = body_top + (body_bottom - body_top - total_message_height) // 2

            for i, line in enumerate(lines[:5]):  # Limite ragionevole
                if not line.strip():
                    continue

                line_bbox = draw.textbbox((0, 0), line, font=message_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                y_pos = message_start_y + i * line_height

                if y_pos > body_bottom - line_height:
                    break

                # Text shadows esatti come card_v5 (3 livelli)
                for dx, dy, color, alpha in [
                    (0, 0, (255, 255, 255), 77),  # 0 0 8px rgba(255,255,255,0.3) ≈ 77/255
                    (0, 0, (0, 0, 0), 153),       # 0 0 15px rgba(0,0,0,0.6) ≈ 153/255
                    (0, 5, (0, 0, 0), 204)        # 0 5px 10px rgba(0,0,0,0.8) ≈ 204/255
                ]:
                    shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    shadow_draw = ImageDraw.Draw(shadow_layer)
                    shadow_draw.text((line_x + dx, y_pos + dy), line, fill=color + (alpha,), font=message_font)
                    img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)

                draw.text((line_x, y_pos), line, fill='#ffffff', font=message_font)

            # === FOOTER ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 100  # padding-top: 60px + padding-bottom: 40px

            draw.text((footer_x, footer_y), footer_text, fill=(140, 140, 140), font=footer_font)  # rgba(255,255,255,0.55) ≈ 140/255

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
