import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Optional


pytesseract.pytesseract.tesseract_cmd = r"C:\Users\gurra\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


def preprocess_image(image_path: str) -> Optional[Image.Image]:
    if not Path(image_path).exists():
        return None
    
    try:
        img = Image.open(image_path)
        img = img.convert('L')
        
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(2.0)
        
        img = img.filter(ImageFilter.SHARPEN)
        
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        return img
    except Exception:
        return None


def perform_ocr(image_path: str) -> str:
    img = preprocess_image(image_path)
    if img is None:
        return ""
    
    try:
        return pytesseract.image_to_string(img, config='--psm 6')
    except Exception:
        return ""
