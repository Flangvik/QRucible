 <p align="center">
 <img src="logo.png" width="300px" alt="QRucible" />
</p>

## QRucible
Tiny Python utility that generates "imageless" QR codes in various formats, useful for evading QR code phishing-specific detections. Partially released with an accompanying blog post and talk at x33fcon 2024. **A lot more** to be added during/after Defcon 32.

## Install

```
pip3 install -r requirements.txt
python3 QRucible.py 

```
## Usage

```

usage: QRucible.py [-h] -u URL [-s SIZE] [-i INPUT] [-o OUTPUT] [--css] [--tables] [--eml]

Tiny Python utility that generates "imageless" QR codes in various formats

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     The URL to be encoded in the QR code.
  -s SIZE, --size SIZE  The box size of the QR code. (default: 40)
  -i INPUT, --input INPUT
                        The input HTML (template) file, replaces the string QR_PLACEHOLDER with the QR code
  -o OUTPUT, --output OUTPUT
                        The output path to an HTML or EML file.
  --css                 Generate QR code using CSS format.
  --tables              Generate QR code using the Table method. Default
  --eml                 Generate an EML file instead of an HTML file.
```

## Example

![QRucible Logo](logo.png)

# Credits

CSS method is based on this example: https://codepen.io/jasonadelia/pen/DwWaNW