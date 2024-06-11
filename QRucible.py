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

def convert_qr_to_table(qr_code_matrix, box_size):
    callPadding = round(box_size / 5)
    html_code = f'<table width="{box_size}px" height="{box_size}px" cellspacing="0" cellpadding="{callPadding}">\n'

    for row in qr_code_matrix:
        html_code += "<tr>\n"
        for cell in row:
            color = "#000000" if cell else "#ffffff"
            html_code += f'<td style="background-color: {color};"></td>\n'
        html_code += "</tr>\n"

    html_code += "</table>"
    return html_code

def convert_qr_to_css(qr_code_matrix, box_size):
    css_code = "<div class=\"qr-code\"></div>\n<style>\n"
    css_code += ".qr-code:before { content: ''; position: absolute; background: #000; width: 1em; height: 1em; }\n"

    box_shadows = []
    for r, row in enumerate(qr_code_matrix):
        for c, cell in enumerate(row):
            if cell:
                box_shadows.append(f"{c}em {r}em #000")

    font_size = box_size / 2.5
    css_code += f".qr-code {{ position: relative; width: 1em; height: 1em; font-size: {font_size}px; box-shadow: {', '.join(box_shadows)}; }}\n"
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

def start(data, filename, box_size, inputFile, css_format, eml_format):
    
    qr_code_html = qr_code_generator(data, box_size, css_format)
    template = "<html><body>QR_PLACEHOLDER</body></html>"
    output = ""
    
    # read the input template file if any
    if inputFile:
        with open(inputFile, 'r') as file:
            template = file.read()
    # if eml format is selected, create an eml file
    if eml_format:
        output = create_eml(data, qr_code_html, template)
    else:
        # if not eml format, create an html file
        output = template.replace('QR_PLACEHOLDER', qr_code_html)
    # check if output filename is provided, if not create a timestamped file
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # if eml format is selected, use the eml extension, otherwise use html
        filename = f'output_{timestamp}.eml' if eml_format else f'output_{timestamp}.html'

    with open(filename, 'w') as f:
        print(f"Output file written to: {filename}")
        f.write(output)

def print_banner():
    f = Figlet(font='slant')
    print(f.renderText('QRucible'))
    print("~Flangvik v0.1")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tiny Python utility that generates "imageless" QR codes in various formats')
    parser.add_argument('-u', '--url', type=str, required=True, help='The URL to be encoded in the QR code.')
    parser.add_argument('-s', '--size', type=int, default=40, help='The box size of the QR code. (default: 40)')
    parser.add_argument('-i', '--input', type=str, help='The input HTML (template) file, replaces the string QR_PLACEHOLDER with the QR code')
    parser.add_argument('-o', '--output', type=str, help='The output path to an HTML or EML file.')
    parser.add_argument('--css', action='store_true', help='Generate QR code using CSS format.')
    parser.add_argument('--tables', action='store_true', default=True, help='Generate QR code using the Table method. Default')
    parser.add_argument('--eml', action='store_true', help='Generate an EML file instead of an HTML file.')
    args = parser.parse_args()

    print_banner()
    start(args.url, args.output, args.size, args.input, args.css, args.eml)
