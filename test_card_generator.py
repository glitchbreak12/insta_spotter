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

    # Messaggi di prova per card normali
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

    # Messaggi di prova per card INFO
    info_messages = [
        {
            "id": 1,
            "text": "🔔 **Importante aggiornamento!**\n\nDa oggi cambiano gli orari di pubblicazione. Le card verranno postate ogni ora invece che ogni 30 minuti.\n\n_Questo migliorerà la qualità del contenuto e ridurrà il traffico sui server._"
        },
        {
            "id": 2,
            "text": "📢 **Nuova funzionalità disponibile!**\n\nÈ ora possibile creare card informative dedicate per annunci importanti.\n\n• Design moderno e professionale\n• Supporto per testo formattato\n• Ottimizzate per Instagram Stories"
        },
        {
            "id": 3,
            "text": "⚡ **Ricorda:**\n\n1. Rispetta sempre la privacy altrui\n2. Non condividere informazioni personali\n3. Mantieni un tono positivo\n4. Segnala contenuti inappropriati\n\n_Insieme rendiamo questa community migliore!_ ✨"
        }
    ]
    
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
    
    # Genera una card per ogni messaggio di prova
    for msg in test_messages:
        message_id = msg["id"]
        message_text = msg["text"]
        
        print(f"\n📝 Generando card per messaggio #{message_id}...")
        print(f"   Testo: {message_text[:50]}...")
        
        try:
            # Genera l'immagine usando from_text
            output_filename = f"test_card_{message_id}.png"
            image_path = generator.from_text(
                message_text=message_text,
                output_filename=output_filename,
                message_id=message_id
            )
            
            if image_path and os.path.exists(image_path):
                print(f"✅ Card generata con successo!")
                print(f"   📁 Percorso: {image_path}")
                file_size = os.path.getsize(image_path) / 1024
                print(f"   📏 Dimensione: {file_size:.2f} KB")
            else:
                print(f"❌ Errore durante la generazione (percorso non valido)")
                
        except Exception as e:
            print(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()

    # Test delle card INFO con il nuovo design
    print(f"\n🔮 Test delle Card INFO (nuovo design)")
    print("=" * 50)

    for msg in info_messages:
        message_id = msg["id"]
        message_text = msg["text"]

        print(f"\n📢 Generando card INFO #{message_id}...")
        print(f"   Testo: {message_text[:60]}...")

        try:
            # Genera l'immagine usando from_text con message_type="info"
            output_filename = f"test_info_card_{message_id}.png"
            image_path = generator.from_text(
                message_text=message_text,
                output_filename=output_filename,
                message_id=message_id,
                message_type="info"  # Questo attiva il template card_info.html
            )

            if image_path and os.path.exists(image_path):
                print(f"✅ Card INFO generata con successo!")
                print(f"   📁 Percorso: {image_path}")
                file_size = os.path.getsize(image_path) / 1024
                print(f"   📏 Dimensione: {file_size:.2f} KB")
            else:
                print(f"❌ Errore durante la generazione (percorso non valido)")

        except Exception as e:
            print(f"❌ Errore: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 50)
    print("✨ Test completato!")
    print(f"📂 Le immagini sono state salvate in: {output_dir.absolute()}")
    print("\n💡 Puoi aprire le immagini per vedere il risultato finale.")
    print("   - Card normali: test_card_*.png")
    print("   - Card INFO: test_info_card_*.png")

if __name__ == "__main__":
    main()
