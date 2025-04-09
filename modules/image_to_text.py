# Libraries
import easyocr

# Initialise the Optical Character Recognition (OCR) reader once
# This is used to scan images and work out the words within it (even handwriting)
reader = easyocr.Reader(['en'], gpu=False)

# Use EasyOCR to extract text from an image uploaded via Flask
def extract_text_from_image(file_storage):
    # Read image from uploaded image file
    image_bytes = file_storage.read()

    # Convert to format EasyOCR expects (NumPy array)
    results = reader.readtext(image_bytes, detail=0)

    # Join text lines together
    extracted_text = " ".join(results)

    # Return the string of the extracted text
    return extracted_text