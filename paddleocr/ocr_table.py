import os
from paddleocr import PaddleOCR, draw_ocr
import pandas as pd

# PaddleOCR initialisieren mit deutschem Modell
ocr = PaddleOCR(use_angle_cls=True, lang='german')

def process_image(image_path):
    # OCR durchführen
    result = ocr.ocr(image_path, cls=True)
    
    # Ergebnisse extrahieren
    data = []
    for line in result:
        row = []
        for word_info in line:
            row.append(word_info[1][0]) # Text extrahieren
        data.append(row)
    
    # Daten in ein DataFrame konvertieren
    df = pd.DataFrame(data)
    
    # Als CSV speichern
    csv_path = os.path.splitext(image_path)[0] + '.csv'
    df.to_csv(csv_path, index=False, header=False)
    print(f"CSV gespeichert als {csv_path}")
    
    # Als Markdown speichern
    md_path = os.path.splitext(image_path)[0] + '.md'
    try:
        md_content = df.to_markdown(index=False, headers=False)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Markdown gespeichert als {md_path}")
    except Exception as e:
        print(f"Fehler beim Speichern als Markdown: {e}")
        print("Speichere stattdessen als einfachen Text...")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(df.to_string(index=False, header=False))
    
    # Als Text speichern
    txt_path = os.path.splitext(image_path)[0] + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        for row in data:
            f.write(' '.join(row) + '\n')
    print(f"Text gespeichert als {txt_path}")

# Beispielaufruf
image_path = '/home/aaron/Anuk_Test_CORS_Pics/Chris_Bilanzvergleich_2013-2017-1.jpg'
process_image(image_path)
