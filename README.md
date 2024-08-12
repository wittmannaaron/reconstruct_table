# Reconstruct Table Project

Dieses Repository enthält verschiedene Ansätze zur Extraktion von Tabellen aus gescannten PDF-Dateien in CSV-Format. Die Skripte sind in verschiedene Ordner unterteilt, je nachdem, welche Technologien und Methoden verwendet wurden.

## Projektübersicht

Das Ziel dieses Projekts ist es, Tabellen aus gescannten Dokumenten in ein maschinenlesbares Format (CSV) zu extrahieren. Dazu wurden unterschiedliche OCR-Technologien und Ansätze zur Datenverarbeitung getestet.

## Verzeichnisstruktur

- **tesseract/**: Enthält Skripte, die Tesseract OCR für die Texterkennung verwenden.
- **docrt/**: Enthält Skripte, die DocRT für die Texterkennung und Tabellenerkennung verwenden.
- **paddleocr/**: Enthält Skripte, die PaddleOCR für die Texterkennung verwenden.

## Skripte

### tesseract/ocr_llm_extraction.py
Dieses Skript verwendet Tesseract OCR, um Text aus gescannten PDFs zu extrahieren und anschließend mit Hilfe eines Sprachmodells Tabellen zu rekonstruieren.

### docrt/ocr_pdf_to_text_neu_v1.py
In diesem Skript wird DocRT verwendet, um Text und Tabellen aus gescannten PDFs zu extrahieren und in Textdateien zu speichern.

### paddleocr/ocr_table.py
Dieses Skript nutzt PaddleOCR, um Tabellen aus gescannten PDFs zu extrahieren und diese als strukturierte Daten in CSV-Dateien zu speichern.

### paddleocr/pdf_table_to_csv_v2.3.py
Ein weiteres Skript, das PaddleOCR verwendet, um Tabellen direkt aus PDFs in CSV-Dateien zu exportieren. Es verbessert den Extraktionsprozess durch fortschrittliche Clustering-Algorithmen.

### paddleocr/test_paddle_ocr.py
Ein Testszenario für die Verwendung von PaddleOCR zur Extraktion von Text und Tabellen aus PDFs.

## Nutzung

Jedes Verzeichnis enthält eigene Skripte für die jeweilige Technologie. Um ein Skript auszuführen, navigieren Sie in das entsprechende Verzeichnis und führen Sie es mit Python aus:
```bash
cd paddleocr
python ocr_table.py
```

## Anforderungen
Python 3.x
Tesseract OCR
PaddleOCR
DocRT

## Weitere Bibliotheken, die in den jeweiligen Skripten spezifiziert sind.
Installation
Um die benötigten Bibliotheken zu installieren, verwenden Sie:
```bash
pip install -r requirements.txt
```


