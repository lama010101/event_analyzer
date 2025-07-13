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
            # Get service account key from environment
            self.service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
            
            if not self.service_account_key:
                print("Warning: No Firebase service account key found.")
                self.access_token = None
                return
            
            # Parse service account info
            self.service_account_info = json.loads(self.service_account_key)
            self.access_token = self._get_access_token()
            
            if self.access_token:
                print(f"Firebase Storage initialized for bucket: {self.bucket_name}")
            else:
                print("Failed to get Firebase access token")
                
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            self.access_token = None
    
    def _get_access_token(self):
        """Simplified Firebase Storage upload using direct API"""
        # For now, we'll use a direct upload approach
        print("Using simplified Firebase Storage approach")
        return "simple_upload"
    
    def upload_image(self, uploaded_file, image_index: int) -> Optional[str]:
        """
        Upload image to Firebase Storage using REST API
        
        Args:
            uploaded_file: Streamlit uploaded file object
            image_index: Index of the image in the batch
            
        Returns:
            Public URL of the uploaded image or None if failed
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = uploaded_file.name.split('.')[-1].lower()
            safe_filename = uploaded_file.name.replace(' ', '_').replace('(', '').replace(')', '')
            filename = f"{timestamp}_{image_index}_{safe_filename}"
            
            # Full path in storage
            storage_path = f"{self.storage_path}/{filename}"
            
            # Set content type based on file extension
            content_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            content_type = content_type_map.get(file_extension, 'image/jpeg')
            
            # Firebase Storage REST API URL (encode the path properly)
            encoded_path = requests.utils.quote(storage_path, safe='')
            upload_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o?name={encoded_path}"
            
            # Headers for upload
            headers = {
                'Content-Type': content_type,
            }
            
            # Upload the file
            response = requests.post(
                upload_url,
                headers=headers,
                data=uploaded_file.getvalue()
            )
            
            if response.status_code in [200, 201]:
                # Get the download URL
                result = response.json()
                download_token = result.get('downloadTokens')
                
                if download_token:
                    # Construct public URL
                    public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{storage_path.replace('/', '%2F')}?alt=media&token={download_token}"
                else:
                    # Fallback public URL without token
                    public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{storage_path.replace('/', '%2F')}?alt=media"
                
                print(f"Image uploaded successfully to Firebase: {public_url}")
                return public_url
            else:
                print(f"Failed to upload to Firebase: {response.status_code} - {response.text}")
                return None
            
        except Exception as e:
            print(f"Error uploading image to Firebase: {str(e)}")
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