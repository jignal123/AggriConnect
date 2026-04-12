import re
import numpy as np
import cv2
import pytesseract
import platform

if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"D:\\Tesseract-OCR\\tesseract.exe"
def fetch_aadhaar(image_bytes):
    # Convert the raw bytes to a numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    
    # Decode the numpy array into an OpenCV image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # If the image fails to load, fail safely
    if img is None:
        return False

    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold for better OCR
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    text = pytesseract.image_to_string(gray)

    # regex pattern
    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    aadhaar_match = re.search(aadhaar_pattern, text)

    aadhaar_no = False
    if aadhaar_match:
        aadhaar_no = aadhaar_match.group().replace(" ", "")

    return aadhaar_no