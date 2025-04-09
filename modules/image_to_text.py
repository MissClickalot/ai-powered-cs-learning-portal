# Libraries
import easyocr

# Initialise the Optical Character Recognition (OCR) reader once
# This is used to scan images and work out the words within it (even handwriting)
reader = easyocr.Reader(['en'], gpu=False)

# Use EasyOCR to extract text from an image uploaded via Flask
def extract_text_from_image(image_path: str) -> str:
    # Convert to format EasyOCR expects (NumPy array)
    results = reader.readtext(image_path, detail=0)

    # Return string of recognised characters
    return " ".join(results)