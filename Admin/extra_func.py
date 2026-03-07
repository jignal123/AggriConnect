import re
import cv2
import pytesseract
import platform

if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"D:\\Tesseract-OCR\\tesseract.exe"
def fetch_aadhaar(image_path):

    img = cv2.imread(image_path)
    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # threshold for better OCR
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
    text = pytesseract.image_to_string(gray)

    aadhaar_pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"
    aadhaar_match = re.search(aadhaar_pattern,text)

    aadhaar_no = False
    if aadhaar_match:
        aadhaar_no = aadhaar_match.group().replace(" ","")

    return aadhaar_no