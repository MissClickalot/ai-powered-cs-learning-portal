# Libraries
import easyocr
import cv2  # To preprocess the image and convert to grayscale (better for handwriting)
import numpy as np

# Initialise the Optical Character Recognition (OCR) reader once
# This is used to scan images and work out the words within it (even handwriting)
reader = easyocr.Reader(['en'], gpu=False)

# Preprocess the image with the context that it is handwritten text
def preprocess_handwritten(image_path: str) -> np.ndarray:
    # Load image in greyscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply Gaussian blur with a 5x5 kernel
    # This smooths the image slightly, helping to remove small specks/grain without blurring the edges of text too much
    # The last parameter (0) tells OpenCV to automatically calculate the blur strength rather than set it manually
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Apply adaptive threshold to sharpen text
    img = cv2.adaptiveThreshold(
        img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return img

# Preprocess the image with the context that it is a printed text image
def preprocess_printed(image_path: str) -> np.ndarray:
    # Load image in greyscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply bilateral filter to smooth out noise while preserving edges
    img = cv2.bilateralFilter(img, 11, 17, 17)

    return img

# Use EasyOCR to extract text from an image uploaded via Flask
def extract_text_from_image(image_path: str, handwritten: bool = True) -> str:

    # Apply suitable preprocessing depending on content type
    if handwritten:
        processed_img = preprocess_handwritten(image_path)
    else:
        processed_img = preprocess_printed(image_path)

    # Perform OCR using EasyOCR on the processed image (NumPy array)
    results = reader.readtext(processed_img, detail=0)

    # DEBUG
    print("Returning cleaned text to frontend.")

    # Return a space-joined string of recognised text
    return " ".join(results)