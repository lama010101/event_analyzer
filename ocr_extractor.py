import pytesseract
import cv2
import numpy as np
from PIL import Image

class OCRExtractor:
    """Handles text extraction from images using Tesseract OCR"""
    
    def __init__(self):
        # Configure Tesseract for better accuracy
        self.config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?:;-()[]{}"\' '
    
    def extract_text(self, image):
        """
        Extract text from image using Tesseract OCR
        Returns cleaned text string
        """
        try:
            # Convert PIL Image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR accuracy
            processed_image = self._preprocess_for_ocr(cv_image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(processed_image, config=self.config)
            
            # Clean and filter the extracted text
            cleaned_text = self._clean_text(text)
            
            return cleaned_text
        
        except Exception as e:
            print(f"Error during OCR extraction: {str(e)}")
            return ""
    
    def _preprocess_for_ocr(self, image):
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def _clean_text(self, text):
        """Clean and filter extracted text"""
        if not text or text.strip() == "":
            return ""
        
        # Split into lines and clean each line
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            
            # Skip very short lines or lines with only special characters
            if len(line) < 2:
                continue
            
            # Filter out lines that are mostly non-alphanumeric
            alphanumeric_count = sum(c.isalnum() for c in line)
            if alphanumeric_count < len(line) * 0.3:
                continue
            
            cleaned_lines.append(line)
        
        # Join cleaned lines
        cleaned_text = ' '.join(cleaned_lines)
        
        # Final cleanup
        cleaned_text = ' '.join(cleaned_text.split())  # Remove extra whitespace
        
        return cleaned_text
    
    def get_text_confidence(self, image):
        """Get confidence scores for detected text"""
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            processed_image = self._preprocess_for_ocr(cv_image)
            
            # Get detailed OCR data including confidence
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence for detected text
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                return avg_confidence
            else:
                return 0
        
        except Exception as e:
            print(f"Error getting text confidence: {str(e)}")
            return 0
