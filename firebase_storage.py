import os
import json
import io
import requests
import base64
from datetime import datetime
from typing import Optional
from PIL import Image

class FirebaseStorageManager:
    """Manages Firebase Storage uploads for historical images using REST API"""
    
    def __init__(self):
        self.bucket_name = "historify-ai.firebasestorage.app"
        self.storage_path = "Analysis"
        self.project_id = "historify-ai"  # Extracted from bucket name
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Storage using REST API"""
        try:
            # Get Firebase config from environment variables
            self.firebase_api_key = os.getenv('Firebase_api_Key')
            self.firebase_project_id = os.getenv('firebase_projectId')
            
            if self.firebase_api_key:
                print(f"Firebase initialized with API key: {self.firebase_api_key[:10]}...")
                print(f"Firebase project ID: {self.firebase_project_id}")
                self.initialized = True
            else:
                print("Warning: No Firebase API key found in environment")
                self.initialized = False
                
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            self.initialized = False
    
    def optimize_image(self, image, max_width_desktop=1200, max_width_mobile=800, quality=85):
        """Optimize image for web usage and convert to WebP"""
        try:
            # Convert to RGB if needed (for WebP compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create desktop version
            desktop_image = image.copy()
            if desktop_image.width > max_width_desktop:
                ratio = max_width_desktop / desktop_image.width
                new_height = int(desktop_image.height * ratio)
                desktop_image = desktop_image.resize((max_width_desktop, new_height), Image.Resampling.LANCZOS)
            
            # Create mobile version  
            mobile_image = image.copy()
            if mobile_image.width > max_width_mobile:
                ratio = max_width_mobile / mobile_image.width
                new_height = int(mobile_image.height * ratio)
                mobile_image = mobile_image.resize((max_width_mobile, new_height), Image.Resampling.LANCZOS)
            
            return desktop_image, mobile_image
            
        except Exception as e:
            print(f"Error optimizing image: {str(e)}")
            return image, image
    
    def upload_image(self, uploaded_file, image_index: int, log_container=None) -> Optional[str]:
        """
        Upload optimized image to Firebase Storage using REST API
        
        Args:
            uploaded_file: Streamlit uploaded file object
            image_index: Index of the image in the batch
            log_container: Streamlit container for logging
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        def log_message(message):
            print(message)
            if log_container:
                log_container.write(f"🔄 {message}")
        
        try:
            log_message("Starting image upload process...")
            
            # Load and optimize image
            log_message("Loading image for optimization...")
            image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            log_message(f"Original image size: {image.width}x{image.height}")
            
            # Optimize image
            desktop_image, mobile_image = self.optimize_image(image)
            log_message(f"Optimized desktop: {desktop_image.width}x{desktop_image.height}")
            log_message(f"Optimized mobile: {mobile_image.width}x{mobile_image.height}")
            
            # Convert to WebP format
            webp_buffer = io.BytesIO()
            desktop_image.save(webp_buffer, format='WebP', quality=85, optimize=True)
            webp_data = webp_buffer.getvalue()
            log_message(f"Converted to WebP, size: {len(webp_data)} bytes")
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = uploaded_file.name.split('.')[0].replace(' ', '_').replace('(', '').replace(')', '')
            filename = f"{timestamp}_{image_index}_{base_filename}.webp"
            storage_path = f"{self.storage_path}/{filename}"
            
            log_message(f"Upload path: {storage_path}")
            
            if not self.initialized:
                log_message("Firebase not initialized, skipping upload")
                return None
            
            # Use Firebase Storage REST API with API key
            upload_url = f"https://firebasestorage.googleapis.com/upload/storage/v1/b/{self.bucket_name}/o"
            
            # Parameters for the upload
            params = {
                'name': storage_path,
                'uploadType': 'media'
            }
            
            if self.firebase_api_key:
                params['key'] = self.firebase_api_key
            
            # Headers for upload
            headers = {
                'Content-Type': 'image/webp',
            }
            
            log_message(f"Uploading to Firebase Storage...")
            log_message(f"URL: {upload_url}")
            
            # Upload the file
            response = requests.post(
                upload_url,
                headers=headers,
                params=params,
                data=webp_data
            )
            
            log_message(f"Upload response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                log_message("✅ Upload successful!")
                
                # Get file name from response
                file_name = result.get('name', storage_path)
                
                # Construct public URL
                encoded_name = requests.utils.quote(file_name, safe='')
                public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{encoded_name}?alt=media"
                
                log_message(f"📂 Public URL: {public_url}")
                return public_url
            else:
                log_message(f"❌ Upload failed: {response.status_code}")
                log_message(f"Response: {response.text}")
                return None
            
        except Exception as e:
            error_msg = f"Error during upload: {str(e)}"
            log_message(f"❌ {error_msg}")
            return None
    
    def upload_pil_image(self, pil_image: Image.Image, filename: str) -> Optional[str]:
        """
        Upload a PIL Image to Firebase Storage
        
        Args:
            pil_image: PIL Image object
            filename: Name for the file
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        if not self.bucket:
            print("Firebase bucket not available")
            return None
            
        try:
            # Convert PIL image to bytes
            img_byte_array = io.BytesIO()
            pil_image.save(img_byte_array, format='JPEG')
            img_byte_array.seek(0)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_filename = f"{timestamp}_{filename}"
            
            # Full path in storage
            storage_path = f"{self.storage_path}/{storage_filename}"
            
            # Create blob reference
            blob = self.bucket.blob(storage_path)
            
            # Upload the file
            blob.upload_from_string(
                img_byte_array.getvalue(),
                content_type='image/jpeg'
            )
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Get the public URL
            public_url = blob.public_url
            
            print(f"PIL Image uploaded successfully: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Error uploading PIL image to Firebase: {str(e)}")
            return None
    
    def list_images(self, limit: int = 100) -> list:
        """List images in the Analysis folder"""
        if not self.bucket:
            return []
            
        try:
            blobs = self.bucket.list_blobs(prefix=f"{self.storage_path}/", max_results=limit)
            image_urls = []
            
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    # Make sure blob is public and get URL
                    try:
                        blob.make_public()
                        image_urls.append({
                            'name': blob.name,
                            'url': blob.public_url,
                            'created': blob.time_created
                        })
                    except:
                        pass
            
            return image_urls
            
        except Exception as e:
            print(f"Error listing images from Firebase: {str(e)}")
            return []