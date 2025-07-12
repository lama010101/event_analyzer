from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from PIL import Image

class VisualCaptioner:
    """Generates visual descriptions using BLIP-2 model"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = "Salesforce/blip-image-captioning-base"
        
        try:
            # Load BLIP model and processor
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            print(f"BLIP model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading BLIP model: {str(e)}")
            self.model = None
            self.processor = None
    
    def generate_caption(self, image):
        """
        Generate a detailed caption for the given image
        Returns a descriptive string about the image content
        """
        if self.model is None or self.processor is None:
            return "Caption generation unavailable - model not loaded"
        
        try:
            # Ensure image is in RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Process image
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=150,
                    num_beams=5,
                    temperature=0.7,
                    do_sample=True,
                    early_stopping=True
                )
            
            # Decode the generated caption
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            # Clean up the caption
            caption = self._enhance_caption(caption)
            
            return caption
        
        except Exception as e:
            print(f"Error generating caption: {str(e)}")
            return "Error generating image caption"
    
    def _enhance_caption(self, caption):
        """Enhance the basic caption with more descriptive language"""
        # Remove any redundant phrases
        caption = caption.replace("a picture of", "").replace("an image of", "")
        caption = caption.strip()
        
        # Capitalize first letter
        if caption:
            caption = caption[0].upper() + caption[1:]
        
        return caption
    
    def generate_detailed_description(self, image):
        """Generate a more detailed description focusing on historical elements"""
        if self.model is None or self.processor is None:
            return "Detailed description unavailable - model not loaded"
        
        try:
            # First generate a basic caption
            basic_caption = self.generate_caption(image)
            
            # For historical images, we can add more context-aware prompting
            # This would ideally use a more sophisticated model, but we'll enhance with BLIP
            inputs = self.processor(
                image, 
                text="A historical photograph showing",
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=200,
                    num_beams=5,
                    temperature=0.8,
                    do_sample=True
                )
            
            detailed_description = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            # Combine basic and detailed descriptions
            if detailed_description != basic_caption:
                return f"{basic_caption}. {detailed_description}"
            else:
                return basic_caption
        
        except Exception as e:
            print(f"Error generating detailed description: {str(e)}")
            return self.generate_caption(image)  # Fallback to basic caption
