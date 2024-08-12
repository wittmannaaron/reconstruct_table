#!/usr/bin/env python3

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

def perform_ocr(image: Image, lang: str) -> str:
    """Führt OCR auf einem Bild mit Tesseract durch."""
    return pytesseract.image_to_string(image, lang=lang)

def chat_with_ollama(prompt, model="llava", url=OLLAMA_URL):
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(f"{url}/api/generate", headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Fehler: {response.status_code} - {response.text}"

def send_image_to_llm(image_path: str, prompt: str) -> Dict:
    """Sendet ein Bild und einen Prompt an das LLM über den CORS-Proxy."""
    # Bilddatei öffnen
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
    
    # Anfrage an den CORS-Proxy senden
    headers = {
        "Content-Type": "application/octet-stream"
    }
    
    # Bereiten Sie die Daten für die Anfrage vor
    data = {
        "model": "llava",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        # Senden Sie zuerst die Bilddaten
        image_response = requests.post(f"{OLLAMA_URL}", headers=headers, data=image_data)
        image_response.raise_for_status()
        
        # Extrahieren Sie die Bild-ID aus der Antwort
        image_id = image_response.json().get('id')
        
        if not image_id:
            raise Exception("Keine Bild-ID in der Antwort erhalten")
        
        # Fügen Sie die Bild-ID zu den Daten hinzu
        data['images'] = [image_id]
        
        # Senden Sie dann die eigentliche Anfrage mit dem Prompt und der Bild-ID
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=data)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Senden der Anfrage an das LLM: {e}")
        if response.text:
            logging.error(f"Serverantwort: {response.text}")
        raise Exception(f"Fehler beim Senden der Anfrage an das LLM: {e}")

def process_with_llm(image_path: str, ocr_text: str, page_num: int) -> Dict[str, str]:
    """Verarbeitet die OCR-Ergebnisse mit dem LLM und gibt strukturierte Daten zurück."""
    try:
        prompt = f"""Analysiere das folgende Bild und den OCR-Text. Das Bild ist ein eingescanntes Dokument, das Text, Tabellen und andere strukturierte Informationen enthalten kann. Der OCR-Text wird unten bereitgestellt. Deine Aufgaben sind:

1. Korrigiere alle OCR-Fehler, die du identifizieren kannst.
2. Identifiziere und formatiere alle Tabellen im Dokument.
3. Erkenne und bewahre die Struktur des Dokuments (Überschriften, Absätze, Listen usw.).
4. Stelle den korrigierten und strukturierten Inhalt in einem Format bereit, das leicht in CSV konvertiert werden kann.

OCR-Text:
{ocr_text}

Bitte gib deine Analyse und den korrigierten, strukturierten Inhalt in folgendem JSON-Format zurück:
{{
    "title": "Titel oder Hauptüberschrift des Dokuments",
    "content": "Der Hauptinhalt des Dokuments, einschließlich korrigiertem Text und Tabellen",
    "tables": [
        {{
            "table_title": "Titel der Tabelle",
            "table_content": "Inhalt der Tabelle als formatierter String"
        }}
    ]
}}

Beachte, dass alle Ausgaben auf Deutsch sein müssen. Bitte stelle sicher, dass deine Antwort ein valides JSON-Objekt ist."""

        # Senden Sie die Anfrage an das LLM
        response = send_image_to_llm(image_path, prompt)
        
        try:
            structured_content = json.loads(response['response'])
            return {
                "page": str(page_num),
                "title": structured_content.get("title", ""),
                "content": structured_content.get("content", ""),
                "tables": json.dumps(structured_content.get("tables", []))
            }
        except json.JSONDecodeError:
            logging.warning(f"Fehler beim Parsen der LLM-Antwort als JSON für Seite {page_num}. Versuche, Informationen zu extrahieren.")
            
            # Fallback: Extrahiere Informationen aus unstrukturiertem Text
            # ... (Rest des Codes bleibt unverändert)

    except Exception as e:
        logging.error(f"Fehler bei der Kommunikation mit der Ollama API für Seite {page_num}: {e}")
        return {"page": str(page_num), "content": ocr_text}

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

if __name__ == "__main__":
    main()
