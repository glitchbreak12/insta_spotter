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

            # === SFONDO STILE card_v5.html ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)

            # Gradiente sfondo sottile come card_v5
            for y in range(height):
                t = y / height
                r = int(0 + 2 * t)
                g = int(0 + 2 * t)
                b = int(0 + 2 * t)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Glows radiali come nel CSS di card_v5
            ambient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            amb_draw = ImageDraw.Draw(ambient)

            # Glow centrale blu a 30% 40%
            for radius, alpha in [(400, 30), (250, 18)]:  # rgba(0, 122, 255, 0.12) ≈ 30/255
                amb_draw.ellipse(
                    [int(width*0.3) - radius, int(height*0.4) - radius,
                     int(width*0.3) + radius, int(height*0.4) + radius],
                    fill=(0, 122, 255, alpha)
                )

            # Glow laterale viola-blu a 70% 60%
            for radius, alpha in [(400, 25), (250, 15)]:  # rgba(88, 86, 214, 0.1) ≈ 25/255
                amb_draw.ellipse(
                    [int(width*0.7) - radius, int(height*0.6) - radius,
                     int(width*0.7) + radius, int(height*0.6) + radius],
                    fill=(88, 86, 214, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), ambient).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === TEMPLATE card_v5.html - CARD GLASS EFFECT ===
            # Card rettangolare con backdrop-filter simulato (rgba(20, 20, 20, 0.8))
            card_x = 90  # padding: 90px come nel template
            card_y = 100  # padding-top: 100px
            card_w = width - 180
            card_h = height - 280  # spazio per footer

            # Box-shadow multi-layer come in card_v5.html
            card_shadow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(card_shadow)

            # Simula: box-shadow: 0 0 10px rgba(0, 122, 255, 0.3), 0 0 40px rgba(0, 122, 255, 0.2), etc.
            shadow_specs = [
                (10, (0, 122, 255, 76)),   # 0.3 * 255 ≈ 76
                (40, (0, 122, 255, 51)),   # 0.2 * 255 ≈ 51
                (80, (0, 122, 255, 38)),   # 0.15 * 255 ≈ 38
                (0, 60, (0, 0, 0, 191))    # 0 20px 60px rgba(0,0,0,0.7) - ultimo valore è offset Y
            ]

            for spec in shadow_specs:
                if len(spec) == 2:
                    blur_radius, color = spec
                    offset_y = 0
                else:
                    blur_radius, color, offset_y = spec

                # Crea un'ellisse sfocata per simulare il blur
                for i in range(blur_radius, 0, -2):
                    alpha = max(0, color[3] - (blur_radius - i) * 3)
                    shadow_draw.rounded_rectangle(
                        [card_x - i, card_y - i + offset_y,
                         card_x + card_w + i, card_y + card_h + i + offset_y],
                        radius=45,
                        fill=(color[0], color[1], color[2], alpha)
                    )

            img = Image.alpha_composite(img.convert('RGBA'), card_shadow).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale con glass effect (rgba(20, 20, 20, 0.8))
            card_main = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_main)

            # Riempimento card con colore semi-trasparente
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                fill=(20, 20, 20, 204)  # rgba(20, 20, 20, 0.8) = 204/255
            )

            # Bordo sottile (rgba(255, 255, 255, 0.08))
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                outline=(255, 255, 255, 20),  # 0.08 * 255 ≈ 20
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

            # === RENDERING TESTO ===

            # BRAND "SPOTTED" in alto centrato
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = card_y + 60

            # Testo bianco con glow blu come card_v5
            for offset in [3, 2, 1]:
                glow_color = (0, 122, 255, max(0, 150 - offset * 50))
                glow_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_img)
                glow_draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=glow_color)
                img = Image.alpha_composite(img.convert('RGBA'), glow_img).convert('RGB')
                draw = ImageDraw.Draw(img)

            draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=(255, 255, 255))

            # MESSAGGIO centrato
            message_y = brand_y + 150
            max_width = card_w - 100

            # Word wrap del messaggio
            words = message_text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=message_font)
                if bbox[2] - bbox[0] <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            # Render delle linee con glow blu
            line_height = 80
            total_text_height = len(lines) * line_height
            start_y = message_y

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=message_font)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2

                # Glow bianco-blu
                for offset in [2, 1]:
                    glow_color = (0, 122, 255, max(0, 100 - offset * 30))
                    glow_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_img)
                    glow_draw.text((text_x, start_y), line, font=message_font, fill=glow_color)
                    img = Image.alpha_composite(img.convert('RGBA'), glow_img).convert('RGB')
                    draw = ImageDraw.Draw(img)

                draw.text((text_x, start_y), line, font=message_font, fill=(255, 255, 255))
                start_y += line_height

            # ID del messaggio in basso a destra
            id_text = f"#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_x = width - 120
            id_y = height - 120

            draw.text((id_x, id_y), id_text, font=id_font, fill=(255, 255, 255, 128))

            # FOOTER "spotted.to" in basso centrato
            footer_text = "spotted.to"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = height - 80

            draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=(255, 255, 255, 180))

            # === RENDERING CARD come card_v5.html ===

            # Carica font
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
                    print(f"⚠️ Errore caricamento font: {e}")

            if not brand_font:
                brand_font = ImageFont.load_default()
                message_font = ImageFont.load_default()
                id_font = ImageFont.load_default()
                footer_font = ImageFont.load_default()

            # === HEADER con BRAND ===
            header_y = 100
            brand_text = "SPOTTED"
            brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (width - brand_width) // 2
            brand_y = header_y

            # Text shadow per brand
            for dx, dy, color, alpha in [
                (0, 2, (0, 0, 0), 204),
                (0, 0, (0, 122, 255), 128),
                (0, 0, (0, 122, 255), 77),
                (0, 0, (0, 122, 255), 25)
            ]:
                shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_layer)
                shadow_draw.text((brand_x + dx, brand_y + dy), brand_text, fill=color + (alpha,), font=brand_font)
                img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)

            draw.text((brand_x, brand_y), brand_text, fill='#ffffff', font=brand_font)

            # === BADGE ID ===
            id_text = f"sp#{message_id}"
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_width = id_bbox[2] - id_bbox[0]
            id_x = (width - id_width) // 2
            id_y = brand_y + 130

            # Badge con glow
            badge_bg = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            badge_draw = ImageDraw.Draw(badge_bg)

            pad_x, pad_y = 30, 12
            badge_width = id_width + (pad_x * 2)
            badge_height = 32 + (pad_y * 2)

            # Glow badge
            for offset, alpha in [(4, 38), (2, 76), (1, 115)]:
                badge_draw.rounded_rectangle(
                    [id_x - pad_x - offset, id_y - pad_y - offset,
                     id_x + id_width + pad_x + offset, id_y + 32 + pad_y + offset],
                    radius=25, fill=(0, 122, 255, alpha)
                )

            # Badge principale
            badge_draw.rounded_rectangle(
                [id_x - pad_x, id_y - pad_y, id_x + id_width + pad_x, id_y + 32 + pad_y],
                radius=25, fill=(0, 122, 255, 30), outline=(0, 122, 255, 64)
            )

            img = Image.alpha_composite(img.convert('RGBA'), badge_bg).convert('RGB')
            draw = ImageDraw.Draw(img)
            draw.text((id_x, id_y), id_text, fill='#5ac8fa', font=id_font)

            # === CARD GLASS ===
            card_x = 90
            card_y = id_y + 100
            card_w = width - 180
            card_h = height - card_y - 150

            card_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_layer)

            # Background card
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45, fill=(20, 20, 20, 204)
            )

            # Bordo card
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45, outline=(255, 255, 255, 20), width=1
            )

            img = Image.alpha_composite(img.convert('RGBA'), card_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # === MESSAGGIO ===
            words = message_text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = draw.textbbox((0, 0), test_line, font=message_font)
                if bbox[2] - bbox[0] <= card_w - 100:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            line_height = 80
            total_height = len(lines) * line_height
            start_y = card_y + (card_h - total_height) // 2

            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=message_font)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2
                y_pos = start_y + i * line_height

                # Text shadows
                for dx, dy, color, alpha in [
                    (0, 0, (255, 255, 255), 77),
                    (0, 0, (0, 0, 0), 153),
                    (0, 5, (0, 0, 0), 204)
                ]:
                    shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    shadow_draw = ImageDraw.Draw(shadow_layer)
                    shadow_draw.text((text_x + dx, y_pos + dy), line, fill=color + (alpha,), font=message_font)
                    img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
                    draw = ImageDraw.Draw(img)

                draw.text((text_x, y_pos), line, fill='#ffffff', font=message_font)

            # === FOOTER ===
            footer_text = "@spottedatbz"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (width - footer_width) // 2
            footer_y = card_y + card_h - 80

            draw.text((footer_x, footer_y), footer_text, fill=(140, 140, 140), font=footer_font)

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
