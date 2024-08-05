import re
import random
import os
import string
import tempfile
from bs4 import BeautifulSoup
from html2image import Html2Image
from PIL import Image
import pytesseract
from pytesseract import Output
import qrcode
import numpy as np
import argparse
import datetime
from pyfiglet import Figlet

def generate_qr(data, box_size):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_code_matrix = np.array(qr.get_matrix())
    return qr_code_matrix

def convert_image_to_table(image_path):
    image = Image.open(image_path).convert("RGB")  # Ensure the image is in RGB mode
    image_width, image_height = image.size
    
    # Adjust cell size to improve resolution
    cell_size = 1  # Set to 1 for higher resolution; increase for smaller images
    
    image_matrix = np.array(image)

    callPadding = 0  # No padding to keep cells tight
    html_code = f'<table style="display:inline-block; border-collapse:collapse; border-spacing:0;">\n'

    for row in image_matrix:
        html_code += "<tr style='padding: 0; margin: 0;'>\n"
        for cell in row:
            # Get the RGB value of the cell
            r, g, b = cell
            color = f'#{r:02x}{g:02x}{b:02x}'
            html_code += f'<td style="padding: 0; margin: 0; background-color: {color}; width: {cell_size}px; height: {cell_size}px;"></td>\n'
        html_code += "</tr>\n"

    html_code += "</table>"
    return html_code

def convert_qr_to_table(qr_code_matrix, box_size):
    # Calculate the padding for the table cells based on the box size
    cell_padding = round(box_size / 5)
    
    # Initialize the HTML code for the table with specified width, height, and cell padding
    html_code = f'<table width="{box_size}px" height="{box_size}px" cellspacing="0" cellpadding="{cell_padding}">\n'

    # Iterate through each row in the QR code matrix
    for row in qr_code_matrix:
        html_code += "<tr>\n"  # Start a new table row
        for cell in row:
            # Determine the cell color based on the QR code matrix value
            color = "#000000" if cell else "#ffffff"
            # Add a table cell with the appropriate background color
            html_code += f'<td style="background-color: {color};"></td>\n'
        html_code += "</tr>\n"  # End the table row

    html_code += "</table>"  # Close the table tag
    return html_code


def convert_qr_to_css(qr_code_matrix, box_size):

    css_code = "<div class=\"qr-code\"></div>\n<style>\n"

    # Add the base style for the QR code block
    css_code += ".qr-code:before { content: ''; position: absolute; background: #000; width: 1em; height: 1em; }\n"

    # Initialize the list to collect box-shadow positions for the QR code pixels
    box_shadows = []
    
    # Iterate through the QR code matrix to determine which cells should be black
    for r, row in enumerate(qr_code_matrix):
        for c, cell in enumerate(row):
            if cell:
                # Add the position of the black cell to the box-shadows list
                box_shadows.append(f"{c}em {r}em #000")

    # Calculate the font size based on the provided box size
    font_size = box_size / 2.5
    
    # Add the main QR code style with calculated box-shadow positions
    css_code += "  .qr-code {\n"
    css_code += "    position: absolute;\n"
    css_code += "    left: 38%;\n"
    css_code += "    display: block;\n"
    css_code += "    margin-left: auto;\n"
    css_code += "    margin-right: auto;\n"
    css_code += f"    width: 1em;\n"
    css_code += f"    height: 1em;\n"
    css_code += f"    font-size: {font_size}px;\n"
    css_code += f"    box-shadow: {', '.join(box_shadows)};\n"
    css_code += "  }\n"
    
    # Close the style tag and return the complete CSS code
    css_code += "</style>"
    return css_code


def qr_code_generator(data, box_size, css_format):
    qr_code_matrix = generate_qr(data, box_size)
    if css_format:
        css_code = convert_qr_to_css(qr_code_matrix, box_size)
        return css_code
    else:
        html_code = convert_qr_to_table(qr_code_matrix, box_size)
        return html_code

def create_eml(data, qr_code_html, template):
    if template:
        html_body = template.replace('QR_PLACEHOLDER', qr_code_html)
    
    eml_content = f"""From: sender@example.com
To: receiver@example.com
Subject: QR Code Email
MIME-Version: 1.0
Content-Type: text/html
X-IOC: BlockMe

{html_body}
"""

    return eml_content

def start(data, filename, box_size, inputFile, css_format, eml_format, obfuscate_keywords):
    qr_code_html = qr_code_generator(data, box_size, css_format)
    template = "<html><body>QR_PLACEHOLDER</body></html>"
    output = ""
    
    # Read the input template file if any
    if inputFile:
        with open(inputFile, 'r') as file:
            template = file.read()

    # Replace QR_PLACEHOLDER with the QR code HTML
    template = template.replace('QR_PLACEHOLDER', qr_code_html)

    # Process obfuscation if keywords are provided
    if obfuscate_keywords:
        keyword_image_paths = process_keywords_in_html(template, obfuscate_keywords)
        for keyword in obfuscate_keywords:
            for image_path in keyword_image_paths[keyword]:
                keyword_table_html = convert_image_to_table(image_path)
                template = replace_one_instance(template, keyword, keyword_table_html)
                os.remove(image_path)
        print("Replaced {} keywords with {} table illustrated images in the HTML template.".format(len(obfuscate_keywords), sum(len(keyword_image_paths[keyword]) for keyword in obfuscate_keywords)))
    # If eml format is selected, create an eml file
    if eml_format:
        output = create_eml(data, qr_code_html, template)
    else:
        # If not eml format, create an html file
        output = template

    # Check if output filename is provided, if not create a timestamped file
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # If eml format is selected, use the eml extension, otherwise use html
        filename = f'output_{timestamp}.eml' if eml_format else f'output_{timestamp}.html'

    with open(filename, 'w') as f:
        f.write(output)

def replace_one_instance(template, keyword, replacement):
    """Replace the first instance of keyword in template with replacement."""
    keyword_re = re.compile(re.escape(keyword), re.IGNORECASE)
    match = keyword_re.search(template)
    if match:
        start, end = match.span()
        template = template[:start] + replacement + template[end:]
    return template





def print_banner():
    f = Figlet(font='slant')
    print(f.renderText('QRucible'))
    print("~Flangvik v0.2")

def add_unique_class_to_keywords(html_content, keywords):
    """Modify HTML to add a unique class around each keyword, ignoring case."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    keyword_count = {keyword: 0 for keyword in keywords}
    
    for keyword in keywords:
        regex = re.compile(re.escape(keyword), re.IGNORECASE)
        for element in soup.find_all(string=regex):
            def replace_with_unique_class(match):
                keyword_count[keyword] += 1
                
                return f'<span class="unique-keyword-{keyword_count[keyword]}">{match.group()}</span>'
            new_html = regex.sub(replace_with_unique_class, str(element))
            element.replace_with(BeautifulSoup(new_html, 'html.parser'))
    print("Added {} unique classes to {} keywords.".format(sum(keyword_count.values()), len(keywords)))
    return str(soup)



def render_html_to_image(html_content):
    """Render the entire HTML content to an image and save to a temp file."""
    hti = Html2Image()
    hti.output_path = tempfile.gettempdir()
    temp_filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".png"
    temp_file_path = os.path.join(tempfile.gettempdir(), temp_filename)
    print("Rendering HTML input to image...")
    hti.screenshot(html_str=html_content, save_as=temp_filename)
    return temp_file_path

def find_keyword_positions_in_image(image_path, keywords):
    """Use OCR to locate the positions of keywords in the image."""
    image = Image.open(image_path)
    custom_config = r'--oem 3 --psm 6'  # Adjust the config if needed
    data = pytesseract.image_to_data(image, config=custom_config, output_type=Output.DICT)
    
    keyword_boxes = {}
    for keyword in keywords:
        keyword_boxes[keyword] = []
        keyword_pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
        
        for i, word in enumerate(data['text']):
            if word != "QR_PLACEHOLDER" and keyword_pattern.fullmatch(word):  # Ensure whole word match and exclude QR_PLACEHOLDER
                keyword_boxes[keyword].append({
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                })
    
    return keyword_boxes







def crop_keyword_from_image(image_path, keyword_box, keyword, count):
    """Crop the keyword portion from the image based on the bounding box and save to a temp file."""
    image = Image.open(image_path)
    x, y, w, h = keyword_box['left'], keyword_box['top'], keyword_box['left'] + keyword_box['width'], keyword_box['top'] + keyword_box['height']
    keyword_image = image.crop((x, y, w, h))
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{keyword}_{count}.png")
    temp_file.close()
    keyword_image.save(temp_file.name)
    return temp_file.name



def process_keywords_in_html(html_content, keywords):
    """Process an array of keywords in the HTML content."""
    
    # Step 1: Add unique class to each keyword instance in the HTML
    modified_html = add_unique_class_to_keywords(html_content, keywords)
    
    # Step 2: Render the modified HTML to an image
    full_image_path = render_html_to_image(modified_html)

    try:
        # Step 3: Use OCR to find the positions of keywords in the image
        keyword_boxes = find_keyword_positions_in_image(full_image_path, keywords)
        
        keyword_image_paths = {keyword: [] for keyword in keywords}
        # Step 4: Iterate over each keyword and its positions
        for keyword, boxes in keyword_boxes.items():
            if boxes:
                for count, box in enumerate(boxes):
                    # Step 5: Crop each instance of the keyword from the image and save it
                    keyword_image_path = crop_keyword_from_image(full_image_path, box, keyword, count)
                    keyword_image_paths[keyword].append(keyword_image_path)
                    print(f"Cropped image for keyword '{keyword}' (instance {count}): {keyword_image_path}")
                
        return keyword_image_paths
    finally:
        # Step 6: Cleanup the full document image
        os.remove(full_image_path)
        print(f"Full document image {full_image_path} removed.")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tiny Python utility that generates "imageless" QR codes in various formats')
    parser.add_argument('-u', '--url', type=str, required=True, help='The URL to be encoded in the QR code.')
    parser.add_argument('-s', '--size', type=int, default=40, help='The box size of the QR code. (default: 40)')
    parser.add_argument('-i', '--input', type=str, help='The input HTML (template) file, replaces the string QR_PLACEHOLDER with the QR code')
    parser.add_argument('-o', '--output', type=str, help='The output path to an HTML or EML file.')
    parser.add_argument('--css', action='store_true', help='Generate QR code using CSS format.')
    parser.add_argument('--tables', action='store_true', default=True, help='Generate QR code using the Table method. Default')
    parser.add_argument('--eml', action='store_true', help='Generate an EML file instead of an HTML file.')
    parser.add_argument('--obfuscate', type=str, nargs='+', help='Keywords to obfuscate by converting them into images.')
    args = parser.parse_args()

    print_banner()
    start(args.url, args.output, args.size, args.input, args.css, args.eml, args.obfuscate)
