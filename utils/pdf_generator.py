# D:\jan-contract\utils\pdf_generator.py

import re
from fpdf import FPDF

def markdown_to_html_for_fpdf(md_text: str) -> str:
    """
    A helper function to convert our simple Markdown (bold and newlines) 
    into simple HTML that FPDF's write_html method can understand.
    """
    # 1. Convert **bold** syntax to <b>bold</b> HTML tags
    # The regex finds text between double asterisks and wraps it in <b> tags.
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', md_text)
    
    # 2. Convert newline characters to <br> HTML tags for line breaks
    text = text.replace('\n', '<br>')
    
    return text

def generate_formatted_pdf(text: str) -> bytes:
    """
    Takes a string containing Markdown and converts it into a well-formatted PDF
    by first converting the Markdown to HTML and then rendering the HTML.
    
    Args:
        text (str): The content of the contract, with Markdown syntax.
        
    Returns:
        bytes: The content of the generated PDF file as a byte string.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Convert our Markdown-style text into simple HTML
    html_content = markdown_to_html_for_fpdf(text)
    
    # Use the more robust write_html() method to render the formatted text.
    # We still need to handle character encoding properly.
    pdf.write_html(html_content.encode('latin-1', 'replace').decode('latin-1'))
    
    # Return the PDF as a 'bytes' object, which Streamlit requires.
    return bytes(pdf.output())