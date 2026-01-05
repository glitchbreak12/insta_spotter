# 🎨 Test Card Generator

Script per testare localmente la generazione delle card immagini con messaggi di prova.

## 📋 Come usare

1. **Esegui lo script:**
   ```bash
   python test_card_generator.py
   ```

2. **Le immagini verranno salvate in:**
   ```
   test_output/
   ├── test_card_1.png
   ├── test_card_2.png
   ├── test_card_3.png
   ├── test_card_4.png
   └── test_card_5.png
   ```

3. **Apri le immagini** per vedere il risultato finale con lo stile Apple 3D semplice.

## ✨ Caratteristiche

- Genera 5 card di prova con messaggi diversi
- Testa word wrap con messaggi lunghi
- Testa caratteri speciali e emoji
- Salva le immagini in una cartella dedicata (`test_output/`)
- Mostra dimensioni e percorsi delle immagini generate

## 🔧 Requisiti

- Python 3.11+
- Pillow (PIL) installato: `pip install Pillow`
- Il progetto deve essere configurato correttamente con `config.py`

## 📝 Messaggi di prova

1. **Messaggio normale** - Test base
2. **Messaggio con emoji** - Test emoji 🎉
3. **Messaggio lungo** - Test word wrap automatico
4. **Caratteri speciali** - Test àèéìòù €$£ @#!? 🚀✨💫
5. **Messaggio breve** - Test layout minimo

## 💡 Personalizzazione

Puoi modificare i messaggi di prova nel file `test_card_generator.py` nella lista `test_messages`.

