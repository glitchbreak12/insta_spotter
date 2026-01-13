#!/usr/bin/env python3
"""
Script per abilitare e testare le funzionalità di Daily Post e Info Cards.
Questo script:
1. Abilita i daily posts nel database
2. Testa la generazione di info cards con il nuovo template v5
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, update_daily_post_settings, get_daily_post_settings
from app.image.generator import ImageGenerator
from datetime import datetime

def enable_daily_posts():
    """Abilita i daily posts nel database."""
    print("🔧 Abilitazione Daily Posts...")

    db = SessionLocal()
    try:
        # Abilita i daily posts
        settings = update_daily_post_settings(
            db=db,
            enabled=True,
            post_time="20:00",
            style="carousel",
            max_messages=20,
            title_template="🌟 Spotted del giorno {date} 🌟\n\nEcco tutti gli spotted della giornata! 💫",
            hashtag_template="#spotted #instaspotter #dailyrecap",
            ai_model="gemini"
        )

        print(f"✅ Daily posts abilitati con successo!")
        print(f"   - Orario: {settings.post_time}")
        print(f"   - Stile: {settings.style}")
        print(f"   - Max messaggi: {settings.max_messages}")
        print(f"   - Modello AI: {settings.ai_model}")

        return True
    except Exception as e:
        print(f"❌ Errore abilitazione daily posts: {e}")
        return False
    finally:
        db.close()

def test_info_card_generation():
    """Testa la generazione di info cards con il nuovo template v5."""
    print("\n🧪 Test generazione Info Card con nuovo template V5...")

    try:
        generator = ImageGenerator()

        # Test con una info card di esempio
        test_title = "📢 Nuovo Aggiornamento"
        test_content = "Abbiamo rilasciato una nuova versione con tante novità! 🎉\n\n- Nuovo design per le info cards\n- Supporto per emoji e formattazione\n- Miglioramenti delle performance\n\nGrazie per il tuo supporto! ❤️"

        output_filename = f"test_info_card_{int(datetime.now().timestamp())}.png"
        image_path = generator.from_text(
            test_content,
            output_filename,
            message_id=999,
            message_type="info",
            title=test_title
        )

        if image_path:
            print(f"✅ Info card generata con successo!")
            print(f"   - Template: card_info.html (V5 style)")
            print(f"   - Percorso: {image_path}")
            print(f"   - Titolo: {test_title}")
            print(f"   - Contenuto: {test_content[:50]}...")
            return True
        else:
            print("❌ Generazione info card fallita")
            return False

    except Exception as e:
        print(f"❌ Errore test info card: {e}")
        return False

def test_daily_post_preview():
    """Testa la generazione di preview per daily posts."""
    print("\n🖼️ Test generazione preview Daily Post...")

    try:
        generator = ImageGenerator()

        # Crea un mock di messaggi per il test
        mock_messages = [
            type('MockMessage', (), {'id': 1, 'text': 'Primo messaggio di test per il daily post'}),
            type('MockMessage', (), {'id': 2, 'text': 'Secondo messaggio con contenuto più lungo per testare il layout'}),
        ]

        # Genera carousel
        base_filename = f"test_daily_{int(datetime.now().timestamp())}"
        title = f"🌟 Spotted del giorno {datetime.now().strftime('%d/%m/%Y')} 🌟"

        image_paths = generator.create_daily_carousel(mock_messages, base_filename, title)

        if image_paths and len(image_paths) > 0:
            print(f"✅ Preview daily post generata con successo!")
            print(f"   - Numero immagini: {len(image_paths)}")
            print(f"   - Prima immagine: {image_paths[0]}")
            print(f"   - Titolo: {title}")
            return True
        else:
            print("❌ Generazione preview daily post fallita")
            return False

    except Exception as e:
        print(f"❌ Errore test daily post preview: {e}")
        return False

def main():
    """Funzione principale."""
    print("🚀 InstaSpotter - Abilitazione e Test Funzionalità")
    print("=" * 50)

    success_count = 0
    total_tests = 3

    # 1. Abilita daily posts
    if enable_daily_posts():
        success_count += 1

    # 2. Testa info cards
    if test_info_card_generation():
        success_count += 1

    # 3. Testa daily post preview
    if test_daily_post_preview():
        success_count += 1

    # Risultati finali
    print("\n" + "=" * 50)
    print(f"📊 RISULTATI: {success_count}/{total_tests} test superati")

    if success_count == total_tests:
        print("🎉 TUTTI I TEST SUPERATI! Le funzionalità sono pronte all'uso.")
        print("\n📋 PROSSIMI PASSI:")
        print("   1. Vai su /admin/daily-post per gestire i daily posts")
        print("   2. Vai su /admin/info-cards per creare info cards")
        print("   3. I daily posts verranno generati automaticamente alle 20:00")
    else:
        print("⚠️ Alcuni test non sono stati superati. Controlla i log per dettagli.")

    return success_count == total_tests

if __name__ == "__main__":
    main()
