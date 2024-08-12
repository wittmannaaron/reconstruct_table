import os
import logging
from typing import List, Dict
import json
import base64
import csv
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import requests
import time

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ollama API-Endpunkt
OLLAMA_URL = "http://sonne.lan:8000"

def get_user_input(prompt: str, default: str) -> str:
    """Fordert den Benutzer zur Eingabe mit einem Standardwert auf."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def set_tesseract_language():
    """Setzt die Sprache für Tesseract OCR."""
    lang = get_user_input("Geben Sie die Sprache für Tesseract ein (z.B. 'deu' für Deutsch)", "deu")
    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Pfad zu Tesseract anpassen, falls nötig
    return lang

def main():
    """Hauptfunktion zur Verarbeitung aller PDF-Dateien im Eingabeverzeichnis."""
    input_dir = get_user_input("Geben Sie das Eingabeverzeichnis ein", "/home/aaron/Anuk_neu_zu_verarbeiten_08_08_24")
    output_dir = get_user_input("Geben Sie das Ausgabeverzeichnis ein", "/home/aaron/Anuk_neu_hochladen_08_08_24")
    tesseract_lang = set_tesseract_language()

    failed_files: List[str] = []

    # Stelle sicher, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # Verarbeite jede PDF-Datei im Eingabeverzeichnis
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.csv")
            
            logging.info(f"Verarbeite: {filename}")
            
            if not process_pdf(input_path, output_path, tesseract_lang):
                failed_files.append(filename)
            else:
                logging.info(f"Erfolgreich verarbeitet und gespeichert: {output_path}")

    # Bericht über fehlgeschlagene Dateien
    if failed_files:
        logging.warning("Die folgenden Dateien konnten nicht verarbeitet werden:")
        for file in failed_files:
            logging.warning(f"- {file}")
    else:
        logging.info("Alle Dateien wurden erfolgreich verarbeitet.")

    logging.info(f"Verarbeitung abgeschlossen. Verarbeitete Dateien befinden sich in: {output_dir}")

def process_pdf(input_file: str, output_file: str, lang: str) -> bool:
    """Verarbeitet eine einzelne PDF-Datei mit OCR und LLM-Verbesserung und speichert sie als CSV."""
    try:
        images = convert_from_path(input_file)
        
        csv_data = []
        
        for i, image in enumerate(images, start=1):
            # OCR durchführen
            ocr_text = perform_ocr(image, lang)
            
            # Bild temporär speichern
            temp_image_path = f"temp_image_{i}.jpg"
            image.save(temp_image_path)
            
            # Mit LLM verarbeiten
            enhanced_content = process_with_llm(temp_image_path, ocr_text, i)
            csv_data.append(enhanced_content)
            
            # Temporäres Bild entfernen
            os.remove(temp_image_path)
            
            # Kleine Verzögerung, um den Server nicht zu überlasten
            time.sleep(1)
        
        # In CSV-Datei schreiben
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["page", "title", "content", "tables"])
            writer.writeheader()
            writer.writerows(csv_data)
        
        logging.info(f"Erfolgreich verarbeitet: {input_file}")
        return True
    except Exception as e:
        logging.error(f"Fehler bei der Verarbeitung von {input_file}: {e}")
        return False

def perform_ocr(image: Image, lang: str) -> str:
    """Führt OCR auf einem Bild mit Tesseract durch."""
    return pytesseract.image_to_string(image, lang=lang)

if __name__ == "__main__":
    main()
