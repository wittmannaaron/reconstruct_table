import fitz  # PyMuPDF
import pytesseract
import pandas as pd
import re
from PIL import Image
import io
import sys

# Funktion zur Extraktion der Tabellen
def extract_tables_from_image(image, lang='deu'):
    # OCR auf dem Bild anwenden
    ocr_result = pytesseract.image_to_string(image, lang=lang)
    
    # Annahme: jede Zeile der Tabelle ist eine Zeile im OCR-Resultat
    rows = ocr_result.split('\n')
    
    # Tabellenstruktur erkennen und in pandas DataFrame umwandeln
    data = []
    for row in rows:
        # Split each row by whitespace or a specific delimiter
        data.append(re.split(r'\s{2,}', row.strip()))
    
    # Entfernen von leeren Zeilen
    data = [row for row in data if any(row)]
    
    # Umwandlung in DataFrame
    df = pd.DataFrame(data)
    
    return df

# Funktion zur Konvertierung von DataFrame zu Markdown
def dataframe_to_markdown(df):
    return df.to_markdown(index=False)

# Hauptfunktion zur Verarbeitung der PDF
def process_pdf(pdf_path, output_md_path, lang='deu'):
    # PDF öffnen
    pdf_document = fitz.open(pdf_path)
    
    all_tables_md = []
    
    # Jede Seite der PDF durchlaufen
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))

        df = extract_tables_from_image(img, lang=lang)
        md_table = dataframe_to_markdown(df)
        all_tables_md.append(md_table)
    
    # Alle Tabellen in eine Markdown-Datei schreiben
    with open(output_md_path, 'w') as md_file:
        for md_table in all_tables_md:
            md_file.write(md_table + '\n\n')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python ocr_table_to_md.py <input_pdf_path> <output_md_path> <lang>")
        sys.exit(1)

    input_pdf_path = sys.argv[1]
    output_md_path = sys.argv[2]
    lang = sys.argv[3]

    process_pdf(input_pdf_path, output_md_path, lang)

