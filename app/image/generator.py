import imgkit
import jinja2
import os
from pathlib import Path
from typing import Optional
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

    def _render_html(self, message_text: str, message_id: int, message_type: str = "spotted", title: str = None) -> str:
        """Carica il template HTML e inserisce il messaggio e l'URL del font."""

        # Scegli il template basato sul tipo di messaggio
        if message_type == "info":
            template_path = "app/image/templates/card_info.html"
            print(f"🎨 [DEBUG] Usando template INFO: {template_path}")
        else:
            template_path = settings.image.template_path
            print(f"🎨 [DEBUG] Usando template SPOTTED: {template_path}")

        template = self.template_env.get_template(os.path.basename(template_path))
        
        # Crea un URL assoluto e corretto per il file del font
        font_path = os.path.abspath(os.path.join(self.template_base_dir, 'fonts', 'Komika_Axis.ttf'))
        font_url = Path(font_path).as_uri()

        return template.render(message=message_text, id=message_id, font_url=font_url, title=title)

    def _generate_with_pil(self, message_text: str, output_path: str, message_id: int, message_type: str = "spotted", title: str = None) -> Optional[str]:
        """Fallback PIL che replica esattamente lo stile card_v5.html con glow 3D."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL non disponibile")

        try:
            # Dimensioni per Instagram Stories (1080x1920)
            width = self.image_width
            height = 1920

            # === SFONDO V5 OTTIMIZZATO - Tema Blu Professionale ===
            img = Image.new('RGB', (width, height), color='#000000')
            draw = ImageDraw.Draw(img)

            # Sfondo con pattern geometrici blu come card_v5 migliorato
            bg_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_layer)

            # Pattern di cerchi concentrici blu come sfondo professionale
            import random
            random.seed(456)  # Seed diverso per V5
            for i in range(12):
                center_x = random.randint(width//6, 5*width//6)
                center_y = random.randint(height//6, 5*height//6)
                base_radius = random.randint(150, 300)

                for r in range(base_radius, 30, -25):
                    alpha = int(50 * (1 - r/base_radius))
                    bg_draw.ellipse(
                        [center_x - r, center_y - r, center_x + r, center_y + r],
                        outline=(0, 122, 255, alpha),
                        width=2
                    )

            # Aggiungi punti luce blu sparsi come stelle digitali
            for i in range(80):
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(2, 6)
                alpha = random.randint(120, 220)
                bg_draw.ellipse([x-size, y-size, x+size, y+size], fill=(0, 122, 255, alpha))

            # Linee geometriche sottili per effetto tech
            for i in range(5):
                start_x = random.randint(0, width//3)
                end_x = random.randint(2*width//3, width)
                y = random.randint(0, height)
                alpha = random.randint(20, 40)
                bg_draw.line([start_x, y, end_x, y], fill=(0, 122, 255, alpha), width=1)

            img = Image.alpha_composite(img.convert('RGBA'), bg_layer).convert('RGB')
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

            # === CARD V5 OTTIMIZZATA - Tema Blu Professionale ===
            card_x = 90  # padding: 90px come nel template
            card_y = 90
            card_w = width - 180
            card_h = height - 180

            # Glow complesso blu professionale
            card_glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(card_glow)

            # Glow multi-layer blu ispirato a design moderno
            glow_colors = [
                (0, 122, 255, 60),   # Blu principale intenso
                (52, 152, 219, 35),  # Blu cielo
                (0, 180, 255, 25),   # Blu chiaro
            ]

            for color_r, color_g, color_b, base_alpha in glow_colors:
                for i in range(30):
                    alpha = max(0, base_alpha - i * 2)
                    offset = i * 2.5
                    glow_draw.rounded_rectangle(
                        [card_x - offset, card_y - offset,
                         card_x + card_w + offset, card_y + card_h + offset],
                        radius=45 + offset//3,
                        outline=(color_r, color_g, color_b, alpha)
                    )

            img = Image.alpha_composite(img.convert('RGBA'), card_glow).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Ombra profonda professionale
            shadow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)

            for i in range(60):
                alpha = int(240 - i * 4)  # Simula box-shadow professionale
                offset_x = i * 1.2
                offset_y = 50 + i * 1.8
                shadow_draw.rounded_rectangle(
                    [card_x + offset_x, card_y + offset_y,
                     card_x + card_w - offset_x, card_y + card_h + offset_y],
                    radius=45,
                    fill=(0, 0, 0, alpha)
                )

            img = Image.alpha_composite(img.convert('RGBA'), shadow_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Card principale con gradiente blu professionale
            card_main = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_main)

            # Gradiente blu professionale da scuro a chiaro
            for y in range(card_h):
                t = y / card_h
                # Gradiente da blu scuro (#1a1a2e) a blu medio (#16213e)
                r = int(26 - 10 * t)  # 1a=26, 16=22
                g = int(26 - 13 * t)  # 1a=26, 21=33 (inverted)
                b = int(46 - 8 * t)   # 2e=46, 3e=62
                card_draw.line(
                    [(card_x, card_y + y), (card_x + card_w, card_y + y)],
                    fill=(r, g, b, 255)
                )

            # Bordo blu luminoso professionale
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=45,
                outline=(0, 180, 255, 220),  # Blu luminoso con alpha
                width=3
            )

            # Effetto shimmer digitale blu
            shimmer_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            shimmer_draw = ImageDraw.Draw(shimmer_layer)

            # Linee diagonali shimmer blu
            for i in range(0, card_w + card_h, 50):
                shimmer_draw.line(
                    [(card_x + i - card_h//2, card_y), (card_x + i - card_h//2 + card_h//6, card_y + card_h)],
                    fill=(100, 200, 255, 40),
                    width=2
                )

            # Punti luce digitali
            for i in range(20):
                x = card_x + random.randint(0, card_w)
                y = card_y + random.randint(0, card_h)
                shimmer_draw.ellipse([x-2, y-2, x+2, y+2], fill=(150, 220, 255, 60))

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

    def _generate_with_playwright(self, message_text: str, output_path: str, message_id: int, message_type: str = "spotted", title: str = None) -> Optional[str]:
        """Screenshot diretto dell'HTML renderizzato in browser reale."""
        if not self.playwright_available:
            raise RuntimeError("Playwright non disponibile")

        import tempfile
        temp_html_path = None

        try:
            # Renderizza l'HTML
            html_content = self._render_html(message_text, message_id, message_type, title)

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

    def from_text(self, message_text: str, output_filename: str, message_id: int, message_type: str = "spotted", title: str = None) -> Optional[str]:
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
                    return self._generate_with_playwright(message_text, output_path, message_id, message_type, title)
                except Exception as pw_error:
                    print(f"❌ Playwright fallito per template complesso: {pw_error}")
                    print("🔄 Fallback a wkhtmltoimage...")
            else:
                print(f"⚠️ Template complesso ({template_name}) ma Playwright non disponibile, uso wkhtmltoimage...")

        # Prima prova con wkhtmltoimage (per template semplici)
        if self.wkhtmltoimage_available:
            try:
                # Renderizza l'HTML con il messaggio e il percorso base
                html_content = self._render_html(message_text, message_id, message_type, title)

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
                        return self._generate_with_playwright(message_text, output_path, message_id, message_type, title)
                    except Exception as pw_error:
                        print(f"❌ Playwright fallito: {pw_error}")
                        print("Cado su PIL come ultimo fallback...")

                        # Terza opzione: PIL come fallback finale
                        if PIL_AVAILABLE:
                            try:
                                print("🔄 Uso PIL come fallback finale...")
                                return self._generate_with_pil(message_text, output_path, message_id, message_type, title)
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
                    return self._generate_with_playwright(message_text, output_path, message_id, message_type, title)
                except Exception as pw_error:
                    print(f"❌ Playwright fallito: {pw_error}")

            # Fallback finale: PIL
            print("🔄 wkhtmltoimage e Playwright non disponibili, uso PIL...")
            if PIL_AVAILABLE:
                try:
                    return self._generate_with_pil(message_text, output_path, message_id, message_type, title)
                except Exception as pil_error:
                    raise RuntimeError(f"Tutti i fallback hanno fallito: {pil_error}") from pil_error
            else:
                raise RuntimeError("ERRORE CRITICO: wkhtmltoimage, Playwright e PIL non disponibili.")

    def create_daily_collage(self, messages: list, output_filename: str, title: str = None) -> Optional[list]:
        """
        Crea un collage giornaliero con più messaggi.
        Ritorna una lista di percorsi di immagini per carousel Instagram.
        """
        if not messages:
            return None

        try:
            print(f"🎨 Creando collage giornaliero con {len(messages)} messaggi...")

            # Dimensioni per Instagram Stories/Carousel
            width, height = 1080, 1920

            # Diversi layout basati sul numero di messaggi
            if len(messages) == 1:
                # Singolo messaggio - usa template normale
                return [self.from_text(messages[0].text, output_filename, messages[0].id)]

            elif len(messages) <= 4:
                # 2x2 grid layout
                return self._create_grid_layout(messages, output_filename, 2, 2, title)

            elif len(messages) <= 6:
                # 2x3 grid layout
                return self._create_grid_layout(messages, output_filename, 2, 3, title)

            elif len(messages) <= 9:
                # 3x3 grid layout
                return self._create_grid_layout(messages, output_filename, 3, 3, title)

            else:
                # Più di 9 messaggi - crea multiple immagini
                return self._create_multi_page_layout(messages, output_filename, title)

        except Exception as e:
            print(f"❌ Errore nella creazione del collage giornaliero: {e}")
            return None

    def create_daily_carousel(self, messages: list, base_filename: str, title: str = None) -> Optional[list]:
        """
        Crea un carousel giornaliero con immagini separate per ogni messaggio.
        La prima immagine contiene il titolo "ecco i post della giornata".
        Ritorna una lista di percorsi di immagini per carousel Instagram.
        """
        if not messages:
            return None

        try:
            print(f"🎨 Creando carousel giornaliero con {len(messages)} messaggi...")

            image_paths = []

            # 1. Crea immagine di introduzione con il titolo
            intro_text = f"📸 {title}\n\nEcco i post della giornata! 🌟"
            intro_filename = f"{base_filename}_intro.png"
            intro_path = self.from_text(intro_text, intro_filename, 0)  # ID 0 per intro
            if intro_path:
                image_paths.append(intro_path)
                print(f"✅ Creata immagine introduzione: {intro_path}")

            # 2. Crea immagini individuali per ogni messaggio
            for i, message in enumerate(messages, 1):
                try:
                    message_filename = f"{base_filename}_{i}.png"
                    message_path = self.from_text(message.text, message_filename, message.id)
                    if message_path:
                        image_paths.append(message_path)
                        print(f"✅ Creata immagine messaggio {i}: {message_path}")
                    else:
                        print(f"⚠️ Saltata immagine messaggio {i} - generazione fallita")
                except Exception as e:
                    print(f"❌ Errore creazione immagine messaggio {i}: {e}")
                    continue

            if len(image_paths) > 1:  # Almeno intro + 1 messaggio
                print(f"🎉 Carousel creato con {len(image_paths)} immagini")
                return image_paths
            else:
                print("❌ Carousel non creato - poche immagini valide")
                return None

        except Exception as e:
            print(f"❌ Errore nella creazione del carousel giornaliero: {e}")
            return None

    def _create_grid_layout(self, messages: list, base_filename: str, rows: int, cols: int, title: str = None) -> list:
        """Crea un layout a griglia per il collage giornaliero."""
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL non disponibile per collage")

        try:
            # Dimensioni per ogni cella
            cell_width = 1080 // cols
            cell_height = 1920 // rows

            # Crea immagine principale
            img = Image.new('RGB', (1080, 1920), color='#000000')
            draw = ImageDraw.Draw(img)

            # Font per il testo
            try:
                font = ImageFont.truetype("app/image/templates/fonts/Komika_Axis.ttf", 32)
                title_font = ImageFont.truetype("app/image/templates/fonts/Komika_Axis.ttf", 48)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()

            # Sfondo con pattern blu professionale
            self._add_professional_background(img, draw)

            # Aggiungi titolo se fornito
            if title:
                # Calcola dimensioni del testo del titolo
                bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = bbox[2] - bbox[0]
                title_x = (1080 - title_width) // 2
                title_y = 50

                # Aggiungi outline al titolo
                for offset_x, offset_y in [(-2,-2), (-2,2), (2,-2), (2,2)]:
                    draw.text((title_x + offset_x, title_y + offset_y), title, font=title_font, fill='#001122')
                draw.text((title_x, title_y), title, font=title_font, fill='#00A0FF')

            # Calcola posizioni per la griglia
            start_y = 200 if title else 100
            cell_padding = 20

            for i, message in enumerate(messages):
                if i >= rows * cols:
                    break

                row = i // cols
                col = i % cols

                x = col * cell_width + cell_padding
                y = start_y + row * cell_height + cell_padding
                w = cell_width - 2 * cell_padding
                h = cell_height - 2 * cell_padding

                # Crea rettangolo semi-trasparente per il messaggio
                overlay = Image.new('RGBA', (w, h), (0, 122, 255, 30))
                img.paste(overlay, (x, y), overlay)

                # Scrivi il testo del messaggio
                self._draw_message_text(draw, message.text, x, y, w, h, font)

            # Salva l'immagine
            output_path = os.path.join(self.output_folder, base_filename)
            img.save(output_path, 'PNG', optimize=True)
            print(f"✅ Collage giornaliero creato: {output_path}")

            return [output_path]

        except Exception as e:
            print(f"❌ Errore nel layout griglia: {e}")
            return None

    def _create_multi_page_layout(self, messages: list, base_filename: str, title: str = None) -> list:
        """Crea multiple immagini per molti messaggi."""
        images = []
        messages_per_page = 6  # 2x3 layout per pagina

        for i in range(0, len(messages), messages_per_page):
            page_messages = messages[i:i + messages_per_page]
            page_title = f"{title} (Parte {i//messages_per_page + 1})" if title else f"Parte {i//messages_per_page + 1}"

            page_filename = f"{base_filename.replace('.png', '')}_part{i//messages_per_page + 1}.png"
            page_images = self._create_grid_layout(page_messages, page_filename, 2, 3, page_title)

            if page_images:
                images.extend(page_images)

        return images if images else None

    def _add_professional_background(self, img: Image, draw: ImageDraw):
        """Aggiunge uno sfondo professionale blu al collage."""
        width, height = img.size

        # Sfondo base blu scuro
        bg = Image.new('RGBA', (width, height), (0, 20, 40, 255))
        img.paste(bg, (0, 0), bg)

        # Pattern di cerchi blu
        import random
        random.seed(42)  # Seed fisso per consistenza

        for i in range(15):
            center_x = random.randint(width//8, 7*width//8)
            center_y = random.randint(height//8, 7*height//8)
            radius = random.randint(100, 200)
            alpha = random.randint(20, 50)

            # Cerchi concentrici
            for r in range(radius, 50, -30):
                draw.ellipse(
                    [center_x - r, center_y - r, center_x + r, center_y + r],
                    outline=(0, 122, 255, alpha),
                    width=1
                )

    def _draw_message_text(self, draw: ImageDraw, text: str, x: int, y: int, w: int, h: int, font):
        """Disegna il testo del messaggio in una cella del collage."""
        # Tronca il testo se troppo lungo
        if len(text) > 150:
            text = text[:147] + "..."

        # Calcola dimensioni del testo
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Ridimensiona font se necessario
        if text_width > w - 20:
            font = ImageFont.truetype("app/image/templates/fonts/Komika_Axis.ttf", 24) if font.size > 24 else font

        # Posiziona il testo
        text_x = x + 10
        text_y = y + 10

        # Aggiungi outline bianco per leggibilità
        for offset_x, offset_y in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill='#FFFFFF')

        # Testo principale blu
        draw.text((text_x, text_y), text, font=font, fill='#00A0FF')

# Esempio di utilizzo (per testare questo file singolarmente)
if __name__ == '__main__':
    generator = ImageGenerator()
    test_message = "Ho spottato una ragazza con un libro di poesie alla fermata del 17. Mi ha sorriso e ha reso la mia giornata migliore. Chissà se leggerà mai questo messaggio."
    
    # Genera l'immagine
    image_path = generator.from_text(test_message, "test_card.png", 1)

    if image_path:
        print(f"\nTest completato. Immagine di prova creata in: {image_path}")
        print("Aprila per vedere il risultato!")
