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

# Import Playwright come alternativa headless quando wkhtmltoimage non funziona
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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

        # Verifica disponibilità Playwright
        self.playwright_available = PLAYWRIGHT_AVAILABLE

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

            # === TEMPLATE CELESTIAL - Rendering OTTIMIZZATO ===
            # Sfondo spaziale con stelle simulate come nel CSS
            stars_layer = Image.new('RGBA', (width, height), (11, 11, 26, 255))  # #0B0B1A
            stars_draw = ImageDraw.Draw(stars_layer)

            # Stelle casuali come nel template CSS
            import random
            random.seed(42)  # Per consistenza
            for i in range(200):  # Molte stelle per effetto spaziale
                x = random.randint(0, width)
                y = random.randint(0, height)
                brightness = random.randint(180, 255)
                size = random.randint(1, 3)
                stars_draw.rectangle([x, y, x+size, y+size], fill=(brightness, brightness, brightness, 220))

            # Nebula gradients come nel CSS
            nebula_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            nebula_draw = ImageDraw.Draw(nebula_layer)

            # Nebula viola centrale (--nebula-purple: #9b59b6)
            for radius in range(350, 100, -15):
                alpha = int(120 * (1 - radius/350))
                nebula_draw.ellipse(
                    [width//2 - radius, height//2 - radius,
                     width//2 + radius, height//2 + radius],
                    fill=(155, 89, 182, alpha)  # #9b59b6
                )

            # Nebula blu ai lati (--nebula-blue: #3498db)
            for radius in range(280, 80, -12):
                alpha = int(100 * (1 - radius/280))
                nebula_draw.ellipse(
                    [width//4 - radius, height//3 - radius,
                     width//4 + radius, height//3 + radius],
                    fill=(52, 152, 219, alpha)  # #3498db
                )

                nebula_draw.ellipse(
                    [3*width//4 - radius, 2*height//3 - radius,
                     3*width//4 + radius, 2*height//3 + radius],
                    fill=(52, 152, 219, alpha)
                )

            # Combina sfondi spaziali
            celestial_bg = Image.alpha_composite(stars_layer, nebula_layer)
            img = Image.alpha_composite(img.convert('RGBA'), celestial_bg).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === CARD CELESTIAL ===
            card_x = 90  # padding: 90px come nel template
            card_y = 90
            card_w = width - 180
            card_h = height - 180

            # Glow complesso come nel template celestial
            card_glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(card_glow)

            # Glow multi-layer ispirato al template
            glow_colors = [
                (0, 122, 255, 48),   # Blu principale
                (155, 89, 182, 32),  # Viola nebula
                (52, 152, 219, 24),  # Blu secondario
            ]

            for color_r, color_g, color_b, base_alpha in glow_colors:
                for i in range(25):
                    alpha = max(0, base_alpha - i * 2)
                    offset = i * 3
                    glow_draw.rounded_rectangle(
                        [card_x - offset, card_y - offset,
                         card_x + card_w + offset, card_y + card_h + offset],
                        radius=45 + offset//2,
                        outline=(color_r, color_g, color_b, alpha)
                    )

            img = Image.alpha_composite(img.convert('RGBA'), card_glow).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Ombra profonda come nel template
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)

            for i in range(50):
                alpha = int(220 - i * 4.4)  # Simula box-shadow
                offset_x = i * 1.5
                offset_y = 40 + i * 2
                shadow_draw.rounded_rectangle(
                    [card_x + offset_x, card_y + offset_y,
                     card_x + card_w - offset_x, card_y + card_h + offset_y],
                    radius=45,
                    fill=(0, 0, 0, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale con gradiente metallico come nel template
            card_main = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_main)

            # Gradiente metallico da #2E2E2E a #1F1F1F
            for y in range(card_h):
                t = y / card_h
                r = int(46 - 15 * t)  # 2E=46, 1F=31
                g = int(46 - 15 * t)
                b = int(46 - 15 * t)
                card_draw.line(
                    [(card_x, card_y + y), (card_x + card_w, card_y + y)],
                    fill=(r, g, b, 255)
                )

            # Bordo dorato come nel template (#d4af37)
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                outline=(212, 175, 55, 204),  # #d4af37 con alpha
                width=4
            )

            # Effetto shimmer metallico come nel CSS
            shimmer_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shimmer_draw = ImageDraw.Draw(shimmer_layer)

            # Linee diagonali shimmer animate
            for i in range(0, card_w + card_h, 60):
                shimmer_draw.line(
                    [(card_x + i - card_h//2, card_y), (card_x + i - card_h//2 + card_h//5, card_y + card_h)],
                    fill=(255, 255, 255, 35),
                    width=3
                )

            img = Image.alpha_composite(img.convert('RGBA'), card_main).convert('RGB')
            img = Image.alpha_composite(img.convert('RGBA'), shimmer_layer).convert('RGB')
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

            # === HEADER CON BRAND E BADGE (esatto come card_v5.html) ===
            header_y = card_y + 50  # padding-top: 50px

            # BRAND "SPOTTED" con text-shadow esatto come card_v5
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = header_y

            # Text shadows esatti come card_v5.html (4 livelli)
            for dx, dy, color, alpha in [
                (0, 0, (0, 122, 255), 128),  # 0 0 10px rgba(0,122,255,0.5) = 128
                (0, 0, (0, 122, 255), 77),   # 0 0 20px rgba(0,122,255,0.3) = 77
                (0, 0, (0, 122, 255), 25),   # 0 0 30px rgba(0,122,255,0.1) = 25
                (0, 2, (0, 0, 0), 204)       # 0 2px 5px rgba(0,0,0,0.8) = 204
            ]:
                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.text((brand_x + dx, brand_y + dy), brand_text, fill=color + (alpha,), font=brand_font)
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)

            draw.text((brand_x, brand_y), brand_text, fill='#ffffff', font=brand_font)

            # BADGE ID esatto come card_v5.html
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + int(95 * 1.1) + 35  # font-size 95px con line-height 1.1 + margin 35px

            badge = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(badge)

            # Padding esatto: 12px 30px
            pad_x, pad_y = 30, 12
            badge_width = id_width + (pad_x * 2)
            badge_height = 32 + (pad_y * 2)  # Altezza base 32px come nel template

            # Box-shadow per il badge
            for shadow_dx, shadow_dy, shadow_color, shadow_alpha in [
                (0, 4, (0, 122, 255), 38)  # 0 4px 20px rgba(0,122,255,0.15) ≈ 38
            ]:
                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.rounded_rectangle(
                    [id_x - pad_x + shadow_dx, id_y - pad_y + shadow_dy,
                     id_x + id_width + pad_x + shadow_dx, id_y + 32 + pad_y + shadow_dy],
                    radius=25,
                    fill=shadow_color + (shadow_alpha,)
                )
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)

            # Badge principale
            bdraw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + 32 + pad_y],
                radius=25,  # border-radius: 25px
                fill=(0, 122, 255, 30),  # background: rgba(0,122,255,0.12)
                outline=(0, 122, 255, 64)  # border: 1px solid rgba(0,122,255,0.25)
            )
            img = Image.alpha_composite(img.convert('RGBA'), badge).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#5ac8fa', font=id_font)  # color: #5ac8fa

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

            # Salva e ottimizza per Instagram
            img.save(output_path, 'PNG', quality=100, optimize=False)
            print(f"✅ Immagine generata con successo (PIL fallback): {output_path}")

            # Ottimizza per Instagram
            optimized_path = self._optimize_for_instagram(output_path)
            return optimized_path

        except Exception as e:
            print(f"❌ Errore PIL fallback: {e}")
            raise

    def _generate_with_playwright(self, message_text: str, output_path: str, message_id: int) -> str | None:
        """Screenshot diretto dell'HTML renderizzato in browser reale."""
        if not self.playwright_available:
            raise RuntimeError("Playwright non disponibile")

        import tempfile
        temp_html_path = None

        try:
            # Renderizza l'HTML
            html_content = self._render_html(message_text, message_id)

            # Crea file HTML temporaneo
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_html_path = f.name

            print(f"📄 File HTML temporaneo creato: {temp_html_path}")

            with sync_playwright() as p:
                # Lancia browser con configurazione ottimale per screenshot
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',  # Permetti file locali
                        '--allow-file-access-from-files',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                try:
                    # Crea pagina con viewport fisso
                    page = browser.new_page(
                        viewport={'width': self.image_width, 'height': 1920},
                        device_scale_factor=1
                    )

                    # Naviga direttamente al file HTML
                    file_url = f'file://{temp_html_path}'
                    page.goto(file_url, wait_until='networkidle', timeout=10000)

                    # Aspetta caricamento completo (font, CSS, animazioni, etc.)
                    page.wait_for_timeout(4000)  # 4 secondi per animazioni e stelle

                    # Verifica rendering completo
                    render_status = page.evaluate('''
                        () => {
                            const body = document.body;
                            const card = document.querySelector('.card');
                            const stars = document.querySelector('#stars');
                            const bg = document.querySelector('.bg-container');

                            return {
                                hasBody: !!body,
                                hasCard: !!card,
                                hasStars: !!stars,
                                hasBg: !!bg,
                                bodyHeight: body ? body.scrollHeight : 0,
                                cardVisible: card ? card.offsetWidth > 0 : false
                            };
                        }
                    ''')

                    print(f"🔍 Render status: {render_status}")

                    if not (render_status.get('hasBody') and render_status.get('hasCard') and render_status.get('bodyHeight', 0) > 500):
                        raise RuntimeError(f"HTML non renderizzato correttamente: {render_status}")

                    # Aspetta ancora un po' per animazioni CSS (stelle, gradienti)
                    page.wait_for_timeout(1000)

                    print("🎨 HTML renderizzato correttamente, catturo screenshot...")

                    # Screenshot della viewport completa
                    page.screenshot(
                        path=output_path,
                        full_page=True,
                        type='png',
                        omit_background=False
                    )

                    print(f"✅ Screenshot HTML diretto completato: {output_path}")

                    # Ottimizza per Instagram dopo la generazione
                    optimized_path = self._optimize_for_instagram(output_path)
                    if optimized_path != output_path:
                        print(f"📱 Ottimizzato per Instagram: {optimized_path}")

                    return optimized_path

                finally:
                    browser.close()

        except Exception as e:
            print(f"❌ Errore screenshot HTML diretto: {e}")
            raise
        finally:
            # Pulisci file temporaneo
            if temp_html_path and os.path.exists(temp_html_path):
                try:
                    os.unlink(temp_html_path)
                    print("🧹 File HTML temporaneo pulito")
                except:
                    pass

    def _optimize_for_instagram(self, image_path: str) -> str:
        """Ottimizza l'immagine per Instagram Stories"""
        try:
            from PIL import Image
            import os

            with Image.open(image_path) as img:
                original_size = os.path.getsize(image_path)

                # Converti a RGB se necessario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    print("🔄 Converted to RGB for Instagram")

                # Ridimensiona se troppo grande (Instagram Stories: max 1080x1920)
                max_width, max_height = 1080, 1920
                if img.size[0] > max_width or img.size[1] > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    print(f"📐 Resized to Instagram specs: {img.size}")

                # Salva con ottimizzazione
                img.save(image_path, 'PNG', optimize=True, quality=95)

                final_size = os.path.getsize(image_path)
                compression_ratio = (original_size - final_size) / original_size * 100
                print(f"📱 Instagram optimization: {original_size} → {final_size} bytes ({compression_ratio:.1f}% reduction)")

                return image_path

        except Exception as e:
            print(f"⚠️ Instagram optimization failed: {e}")
            return image_path

    def from_text(self, message_text: str, output_filename: str, message_id: int) -> str | None:
        """
        Genera un'immagine PNG da un testo con gerarchia di metodi:

        1. wkhtmltoimage (principale - rendering nativo)
        2. Playwright (alternativa headless - rendering perfetto CSS)
        3. PIL (fallback finale - simulazione PIL)

        Args:
            message_text: Il testo da inserire nell'immagine.
            output_filename: Il nome del file di output (es. 'spotted_123.png').
            message_id: L'ID del messaggio, da passare al template.

        Returns:
            Il percorso del file generato, o None se si verifica un errore.
        """
        # Definisce il percorso completo per il file di output
        output_path = os.path.join(self.output_folder, output_filename)

        # Verifica se stiamo usando un template complesso che richiede Playwright
        template_name = os.path.basename(settings.image.template_path)
        is_complex_template = 'celestial' in template_name or 'prestige' in template_name or 'voltaic' in template_name

        # Per template complessi, salta wkhtmltoimage e usa direttamente Playwright
        if is_complex_template:
            if self.playwright_available:
                print(f"🎨 Template complesso rilevato ({template_name}), uso Playwright per rendering perfetto...")
                try:
                    return self._generate_with_playwright(message_text, output_path, message_id)
                except Exception as pw_error:
                    print(f"❌ Playwright fallito per template complesso: {pw_error}")
                    print("🔄 Fallback a wkhtmltoimage...")
            else:
                print(f"⚠️ Template complesso ({template_name}) ma Playwright non disponibile, uso wkhtmltoimage...")

        # Prima prova con wkhtmltoimage (per template semplici)
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

                # Ottimizza per Instagram anche le immagini wkhtmltoimage
                optimized_path = self._optimize_for_instagram(output_path)
                return optimized_path

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

                # Se wkhtmltoimage fallisce, prova Playwright come seconda opzione
                if self.playwright_available:
                    try:
                        print("🎭 Provo Playwright per rendering HTML accurato...")
                        return self._generate_with_playwright(message_text, output_path, message_id)
                    except Exception as pw_error:
                        print(f"❌ Playwright fallito: {pw_error}")
                        print("Cado su PIL come ultimo fallback...")

                # Terza opzione: PIL come fallback finale
                if PIL_AVAILABLE:
                    try:
                        print("🔄 Uso PIL come fallback finale...")
                        return self._generate_with_pil(message_text, output_path, message_id)
                    except Exception as pil_error:
                        print(f"❌ Anche PIL ha fallito: {pil_error}")
                        raise RuntimeError(f"Tutti i metodi hanno fallito. wkhtmltoimage: {e}, Playwright: {pw_error if 'pw_error' in locals() else 'N/A'}, PIL: {pil_error}") from pil_error
                else:
                    raise RuntimeError(f"wkhtmltoimage fallito e nessun fallback disponibile: {e}") from e
        else:
            # wkhtmltoimage non disponibile, prova prima Playwright poi PIL
            if self.playwright_available:
                try:
                    print("🎭 wkhtmltoimage non disponibile, provo Playwright...")
                    return self._generate_with_playwright(message_text, output_path, message_id)
                except Exception as pw_error:
                    print(f"❌ Playwright fallito: {pw_error}")

            # Fallback finale: PIL
            print("🔄 wkhtmltoimage e Playwright non disponibili, uso PIL...")
            if PIL_AVAILABLE:
                try:
                    return self._generate_with_pil(message_text, output_path, message_id)
                except Exception as pil_error:
                    raise RuntimeError(f"Tutti i fallback hanno fallito: {pil_error}") from pil_error
            else:
                raise RuntimeError("ERRORE CRITICO: wkhtmltoimage, Playwright e PIL non disponibili.")

# Esempio di utilizzo (per testare questo file singolarmente)
if __name__ == '__main__':
    generator = ImageGenerator()
    test_message = "Ho spottato una ragazza con un libro di poesie alla fermata del 17. Mi ha sorriso e ha reso la mia giornata migliore. Chissà se leggerà mai questo messaggio."

    # Genera l'immagine
    image_path = generator.from_text(test_message, "test_card.png", 1)

    if image_path:
        print(f"\nTest completato. Immagine di prova creata in: {image_path}")
        print("Aprila per vedere il risultato!")
