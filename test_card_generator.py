#!/usr/bin/env python3
"""
Script per testare localmente la generazione delle card immagini.
Esegui: python test_card_generator.py
"""

import os
import sys
from pathlib import Path

# Aggiungi il percorso del progetto al PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.image.generator import ImageGenerator

def main():
    """Genera una card di prova con un messaggio di esempio."""
    
    # Crea cartella di output se non esiste
    output_dir = project_root / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Messaggi di prova
    test_messages = [
        {
            "id": 1,
            "text": "Ciao a tutti! Questo è un messaggio di prova per testare la generazione delle card."
        },
        {
            "id": 2,
            "text": "Spotto qualcuno che oggi ha fatto qualcosa di speciale! 🎉"
        },
        {
            "id": 3,
            "text": "Messaggio più lungo per testare il word wrap e vedere come viene gestito il testo quando è molto lungo e deve andare a capo automaticamente su più righe."
        },
        {
            "id": 4,
            "text": "Test con caratteri speciali: àèéìòù €$£ @#!? 🚀✨💫"
        },
        {
            "id": 5,
            "text": "Messaggio breve."
        }
    ]

    test_templates = ["card_v5_emoji_fix.html"]
    
    print("🎨 Generatore Card di Prova")
    print("=" * 50)
    
    # Inizializza il generatore
    try:
        generator = ImageGenerator()
        # Sostituisci temporaneamente la cartella di output
        original_output = generator.output_folder
        generator.output_folder = str(output_dir)
        print("✅ Generatore inizializzato correttamente")
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione: {e}")
        return
    
    # Genera una card per ogni messaggio di prova e per ogni template
    for template_name in test_templates:
        print(f"\n--- Generando card con template: {template_name} ---")
        for msg in test_messages:
            message_id = msg["id"]
            message_text = msg["text"]
            
            print(f"\n📝 Generando card per messaggio #{message_id}...")
            print(f"   Testo: {message_text[:50]}...")
            
            try:
                # Genera l'immagine usando from_text
                output_filename = f"test_card_{template_name.replace('.html', '')}_{message_id}.png"
                image_path = generator.from_text(
                    message_text=message_text,
                    output_filename=output_filename,
                    message_id=message_id,
                    template_name=template_name # Passa il nome del template
                )
                
                if image_path and os.path.exists(image_path):
                    print(f"✅ Card generata con successo!")
                    print(f"   📁 Percorso: {image_path}")
                    file_size = os.path.getsize(image_path) / 1024
                    print(f"   📏 Dimensione: {file_size:.2f} KB")
                else:
                    print(f"❌ Errore durante la generazione (percorso non valido o fallback fallito)")
                    
            except Exception as e:
                print(f"❌ Eccezione durante la generazione della card #{message_id} con template {template_name}:")
                import traceback
                traceback.print_exc()    
    print("\n" + "=" * 50)
    print("✨ Test completato!")
    print(f"📂 Le immagini sono state salvate in: {output_dir.absolute()}")
    print("\n💡 Puoi aprire le immagini per vedere il risultato finale.")

if __name__ == "__main__":
    main()

