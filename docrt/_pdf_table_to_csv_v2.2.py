import cv2
import doctr
import pytesseract
import numpy as np
import pandas as pd
from pdf2image import convert_from_path
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from PIL import Image
from io import BytesIO
from sklearn.cluster import DBSCAN

def convert_pdf_to_images_and_grayscale(pdf_path):
    """
    Converts each page of the given PDF to a grayscale image and returns a list of images.
    Input:
    - pdf_path: Path to the PDF file
    Output:
    - List of grayscale images (each image representing a page in the PDF)
    """
    # Convert PDF to list of images
    images = convert_from_path(pdf_path)

    grayscale_images = []
    for image in images:
        # Convert PIL Image to NumPy array
        image_np = np.array(image)

        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        
        grayscale_images.append(gray_image)

    return images # Das habe ich von gayscale_images nach images geändert, da wir images erwarten


def correct_image_orientation(image):
    """
    Corrects the orientation of the given image using OpenCV.
    Input:
    - image: The image to be corrected (PIL Image)
    Output:
    - Rotated image that is aligned properly (NumPy array)
    """
    # Convert PIL image to NumPy array
    image_np = np.array(image)

    # Debug output: Check the shape of the image
    print(f"[DEBUG] Image shape: {image_np.shape}")

    # Check if the image is already grayscale or not
    if len(image_np.shape) == 2:  # Image is already in grayscale
        gray = image_np
    else:
        # Convert image to grayscale
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    
    # Use Canny edge detection to find edges in the image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Use Hough Line Transformation to find lines in the image
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    # Calculate the angle of the lines
    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta * 180 / np.pi) - 90
            angles.append(angle)
        
        # Find the median angle
        median_angle = np.median(angles)
    else:
        # If no lines are found, assume no rotation
        median_angle = 0

    # Debug output: Show the calculated angle
    print(f"[DEBUG] Calculated rotation angle: {median_angle} degrees")

    # Rotate the image to correct the orientation
    (h, w) = image_np.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated_image = cv2.warpAffine(image_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated_image


def segment_image_into_lines(image):
    """
    Segments the given image into individual lines.
    Input:
    - image: The image to be segmented (NumPy array)
    Output:
    - List of images, each containing a single line of the original image
    """
    # Convert image to grayscale (if not already)
    if len(image.shape) == 3:  # If the image has 3 channels (color image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Apply a binary threshold to the image
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Sum up the pixels in each row to get the horizontal projection
    horizontal_projection = np.sum(binary, axis=1)

    # Detect where lines of text are located based on the projection
    line_indices = np.where(horizontal_projection > 0)[0]
    
    # Group the indices into separate lines
    lines = []
    start_index = line_indices[0]
    
    for i in range(1, len(line_indices)):
        if line_indices[i] > line_indices[i-1] + 1:
            lines.append((start_index, line_indices[i-1]))
            start_index = line_indices[i]
    
    lines.append((start_index, line_indices[-1]))  # Append the last line

    # Debug output: Number of lines detected
    print(f"[DEBUG] Number of lines detected: {len(lines)}")

    # Crop the lines from the image
    line_images = []
    for i, (start, end) in enumerate(lines):
        line_image = image[start:end, :]
        line_images.append(line_image)
        # Optional debug: print height of each line
        print(f"[DEBUG] Line {i + 1} height: {end - start} pixels")

    return line_images


def extract_table_structure(image, ocr_results):
    """
    Analyzes the given image and OCR results to extract table structure, identifying columns and rows.
    Input:
    - image: The image to be analyzed (NumPy array)
    - ocr_results: List of dictionaries containing the OCR text and positions
    Output:
    - DataFrame with the structured table data
    """
    table_data = []

    for line_data in ocr_results:
        if not line_data:  # Skip empty lines
            continue
        
        # Extract the x-coordinates (left position) of each word
        x_positions = [word_data['geometry'][0][0] for word_data in line_data]
        
        # Use DBSCAN clustering to group words into columns based on their x-coordinates
        clustering = DBSCAN(eps=100, min_samples=1).fit(np.array(x_positions).reshape(-1, 1))
        labels = clustering.labels_
        
        # Group words by their cluster label (column)
        columns = {}
        for word_data, label in zip(line_data, labels):
            if label not in columns:
                columns[label] = []
            columns[label].append(word_data['text'])
        
        # Create a row with the grouped words, sorting columns by their x-position
        row = [' '.join(columns[label]) for label in sorted(columns)]
        table_data.append(row)

    # Convert the list of rows into a DataFrame
    df = pd.DataFrame(table_data)

    # Debug output: Show the structure of the extracted table
    print(f"[DEBUG] Extracted table structure:\n{df}")

    return df


def ocr_on_lines(lines):
    """
    Applies OCR on the segmented lines using Doctr.
    Input:
    - lines: List of images, each containing a single line (as NumPy arrays)
    Output:
    - List of dictionaries containing the extracted text and its position
    """
    # Initialize the Doctr OCR predictor
    predictor = ocr_predictor(pretrained=True)
    
    extracted_data = []

    for idx, line_image in enumerate(lines):
        # Convert NumPy array to PIL Image
        pil_image = Image.fromarray(line_image)
        
        # Save the PIL Image to a BytesIO object as a single-page PDF
        pdf_buffer = BytesIO()
        pil_image.save(pdf_buffer, format='PDF')
        pdf_buffer.seek(0)  # Reset the buffer position to the beginning
        
        # Convert the BytesIO object (PDF) to a DocumentFile that Doctr can process
        doc = DocumentFile.from_pdf(pdf_buffer)
        
        # Apply OCR to the line image
        result = predictor(doc)

        # Extract text and positions directly in a more structured way
        line_data = [
            {
                'text': word.value,
                'confidence': word.confidence,
                'geometry': word.geometry
            }
            for page in result.pages
            for block in page.blocks
            for line in block.lines
            for word in line.words
        ]

        # Skip empty lines
        if line_data:
            extracted_data.append(line_data)
        
        # Debug output: Print the extracted text for this line, or note if it's empty
        detected_text = ' '.join([word['text'] for word in line_data])
        print(f"[DEBUG] Line {idx + 1}: {detected_text if detected_text else 'EMPTY'}")

    return extracted_data


def save_to_csv(extracted_data, output_file):
    """
    Saves the extracted data to a CSV file.
    Input:
    - extracted_data: Data extracted from the images
    - output_file: Path to the output CSV file
    Output:
    - CSV file saved at the specified path
    """
    # Placeholder: Implement saving logic
    pass


def process_pdf(pdf_path, output_csv):
    # Konvertiere PDF in Bilder und richte sie aus
    images = convert_pdf_to_images_and_grayscale(pdf_path)
    all_extracted_data = []

    for image in images:
        corrected_image = correct_image_orientation(image)
        lines = segment_image_into_lines(corrected_image)
        ocr_results = ocr_on_lines(lines)
        
        # Aufruf der Funktion mit den richtigen Argumenten
        structured_data = extract_table_structure(corrected_image, ocr_results)
        all_extracted_data.append(structured_data)

    # Speichern der Daten in einer CSV-Datei
    save_to_csv(all_extracted_data, output_csv)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_pdf> <output_csv>")
    else:
        pdf_path = sys.argv[1]
        output_csv = sys.argv[2]
        process_pdf(pdf_path, output_csv)

