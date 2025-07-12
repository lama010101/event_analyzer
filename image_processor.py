import cv2
import numpy as np
from PIL import Image
import io

class ImageProcessor:
    """Handles image preprocessing operations"""
    
    def __init__(self):
        pass
    
    def preprocess_image(self, uploaded_file):
        """
        Preprocess uploaded image:
        - Resize to 1024px wide
        - Normalize color space
        - Enhance contrast if black and white
        """
        # Convert uploaded file to PIL Image
        image = Image.open(uploaded_file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to 1024px wide while maintaining aspect ratio
        original_width, original_height = image.size
        if original_width > 1024:
            new_width = 1024
            new_height = int((new_width * original_height) / original_width)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to OpenCV format for processing
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Check if image is grayscale/black and white
        if self._is_grayscale(cv_image):
            # Enhance contrast for B&W images
            cv_image = self._enhance_contrast(cv_image)
        
        # Normalize color space
        cv_image = self._normalize_colors(cv_image)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        return processed_image
    
    def _is_grayscale(self, image):
        """Check if image is grayscale"""
        # Calculate the standard deviation of each channel
        b, g, r = cv2.split(image)
        std_b = np.std(b)
        std_g = np.std(g)
        std_r = np.std(r)
        
        # If all channels have similar distributions, it's likely grayscale
        threshold = 5.0
        return (abs(std_b - std_g) < threshold and 
                abs(std_g - std_r) < threshold and 
                abs(std_b - std_r) < threshold)
    
    def _enhance_contrast(self, image):
        """Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)"""
        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to BGR
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_bgr
    
    def _normalize_colors(self, image):
        """Normalize color values"""
        # Convert to float32 for processing
        normalized = image.astype(np.float32) / 255.0
        
        # Apply gamma correction for better visibility
        gamma = 1.2
        normalized = np.power(normalized, 1.0 / gamma)
        
        # Convert back to uint8
        normalized = (normalized * 255).astype(np.uint8)
        
        return normalized
    
    def image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        return image_base64
