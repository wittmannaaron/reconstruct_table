#!/usr/bin/env python3

import os
import subprocess
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_input(prompt: str, default: str) -> str:
    """
    Prompt the user for input with a default value.
    
    Args:
    prompt (str): The prompt to display to the user.
    default (str): The default value to use if the user doesn't provide input.
    
    Returns:
    str: The user's input or the default value.
    """
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def process_pdf(input_file: str, output_file: str, language: str, hocr: bool = False) -> bool:
    """
    Process a single PDF file using OCRmyPDF with enhanced table recognition.
    
    Args:
    input_file (str): Path to the input PDF file.
    output_file (str): Path to the output text file.
    language (str): Language code for OCR.
    hocr (bool): Whether to output hOCR format instead of plain text.
    
    Returns:
    bool: True if processing was successful, False otherwise.
    """
    try:
        # Base command
        cmd = [
            "ocrmypdf",
            "-l", language,
            "--sidecar", output_file,
            "--output-type", "none",
            "--tesseract-config", "tessedit_pageseg_mode=6",
            input_file,
            "/dev/null"  # Discard PDF output
        ]
        
        # Add hOCR output if requested
        if hocr:
            cmd.extend(["--sidecar-format", "hocr"])
        
        # Run OCRmyPDF command
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"Successfully processed: {input_file}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {input_file}: {e}")
        logging.error(f"OCRmyPDF stderr: {e.stderr}")
        return False

def main():
    """
    Main function to process all PDF files in the input directory.
    """
    # Get user input for directories and language
    input_dir = get_user_input("Enter input directory", "/home/aaron/Anuk_neu_zu_verarbeiten_08_08_24")
    output_dir = get_user_input("Enter output directory", "/home/aaron/Anuk_neu_hochladen_08_08_24")
    language = get_user_input("Enter language code for OCR", "deu")
    hocr_output = get_user_input("Use hOCR output for better table recognition? (yes/no)", "no").lower() == "yes"

    failed_files: List[str] = []

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process each PDF file in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_ext = ".hocr" if hocr_output else ".txt"
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}{output_ext}")
            
            logging.info(f"Processing: {filename}")
            
            if not process_pdf(input_path, output_path, language, hocr_output):
                failed_files.append(filename)

    # Report on failed files
    if failed_files:
        logging.warning("The following files could not be processed:")
        for file in failed_files:
            logging.warning(f"- {file}")
    else:
        logging.info("All files processed successfully.")

if __name__ == "__main__":
    main()
