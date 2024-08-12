#!/usr/bin/env python3

import os
import subprocess
import logging
from typing import List
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_input(prompt: str, default: str) -> str:
    """Prompt the user for input with a default value."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def process_pdf(input_file: str, output_file: str, language: str) -> bool:
    """Process a single PDF file using OCR and convert to Markdown."""
    try:
        # Convert PDF to images
        images = convert_from_path(input_file)
        
        markdown_content = f"# {os.path.basename(input_file)}\n\n"
        
        for i, image in enumerate(images):
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=language)
            
            # Process the text to identify potential tables
            lines = text.split('\n')
            table_content = []
            in_table = False
            
            for line in lines:
                if re.match(r'^\s*[\-+]+\s*$', line):  # Possible table separator
                    in_table = True
                    table_content.append(line)
                elif in_table and '|' in line:  # Possible table row
                    table_content.append(line)
                else:
                    if in_table:
                        # End of table, convert to Markdown table
                        markdown_content += "\n" + convert_to_markdown_table(table_content) + "\n"
                        table_content = []
                        in_table = False
                    markdown_content += line + "\n"
            
            # Add page separator
            if i < len(images) - 1:
                markdown_content += "\n---\n\n"
        
        # Write to Markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logging.info(f"Successfully processed: {input_file}")
        return True
    except Exception as e:
        logging.error(f"Error processing {input_file}: {e}")
        return False

def convert_to_markdown_table(table_content: List[str]) -> str:
    """Convert detected table content to Markdown table format."""
    if not table_content:
        return ""
    
    # Clean up and standardize separators
    table_content = [re.sub(r'[\-+]+', '|', line).strip() for line in table_content if line.strip()]
    
    # Ensure all rows have the same number of columns
    max_cols = max(line.count('|') for line in table_content)
    table_content = [line + '|' * (max_cols - line.count('|')) for line in table_content]
    
    # Add header separator
    if len(table_content) > 1:
        table_content.insert(1, '|' + '|'.join(['---' for _ in range(max_cols)]) + '|')
    
    return '\n'.join(table_content)

def main():
    """Main function to process all PDF files in the input directory."""
    input_dir = get_user_input("Enter input directory", "/home/aaron/Anuk_neu_zu_verarbeiten_08_08_24")
    output_dir = get_user_input("Enter output directory", "/home/aaron/Anuk_neu_hochladen_08_08_24")
    language = get_user_input("Enter language code for OCR", "deu")

    failed_files: List[str] = []

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process each PDF file in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.md")
            
            logging.info(f"Processing: {filename}")
            
            if not process_pdf(input_path, output_path, language):
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
