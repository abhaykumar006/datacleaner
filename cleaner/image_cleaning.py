from PIL import Image, ImageEnhance
import pytesseract
import numpy as np

# 🔥 IMPORTANT (OCR path)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def process_image(file):
    try:
        # ================= LOAD IMAGE =================
        img = Image.open(file)

        # ================= PROPERTIES =================
        width, height = img.size
        mode = img.mode
        format_type = img.format

        properties = {
            "width": width,
            "height": height,
            "mode": mode,
            "format": format_type
        }

        # ================= ENHANCEMENT =================
        # Sharpness
        img = ImageEnhance.Sharpness(img).enhance(2.0)

        # Contrast
        img = ImageEnhance.Contrast(img).enhance(1.5)

        # Brightness
        img = ImageEnhance.Brightness(img).enhance(1.2)

        # ================= OCR =================
        try:
            text = pytesseract.image_to_string(img)
        except:
            text = "OCR failed"

        return img, text, properties

    except Exception as e:
        print("IMAGE ERROR:", e)
        return None, None, None