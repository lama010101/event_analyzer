#!/usr/bin/env python3
"""
Test Firebase Storage upload functionality
"""
import os
import requests
from PIL import Image
import io
from datetime import datetime

# Firebase configuration
FIREBASE_API_KEY = "AIzaSyAnGNZRZ2fjRoiylCXFLH1Wm5foE0iewFo"
BUCKET_NAME = "historify-ai.firebasestorage.app"
STORAGE_PATH = "Analysis"

def create_test_image():
    """Create a small test image"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Convert to WebP
    webp_buffer = io.BytesIO()
    img.save(webp_buffer, format='WebP', quality=85)
    return webp_buffer.getvalue()

def test_firebase_upload():
    """Test Firebase Storage upload with authentication"""
    print("Testing Firebase Storage upload with authentication...")
    
    # Create test image data
    test_data = create_test_image()
    print(f"Created test image: {len(test_data)} bytes")
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_{timestamp}.webp"
    storage_path = f"{STORAGE_PATH}/{filename}"
    
    print(f"Upload path: {storage_path}")
    
    # Step 1: Authenticate with Firebase (using correct endpoint)
    print("\n--- Step 1: Firebase Authentication ---")
    auth_url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key={FIREBASE_API_KEY}"
    
    try:
        auth_response = requests.post(auth_url, json={"returnSecureToken": True})
        print(f"Auth status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            id_token = auth_data.get('idToken')
            print(f"✅ Authentication successful, token: {id_token[:20]}...")
            
            # Step 2: Upload with Bearer token
            print("\n--- Step 2: Upload with Bearer token ---")
            upload_url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET_NAME}/o"
            
            params = {
                'name': storage_path,
                'uploadType': 'media'
            }
            
            headers = {
                'Content-Type': 'image/webp',
                'Authorization': f'Bearer {id_token}'
            }
            
            print(f"Upload URL: {upload_url}")
            print(f"Params: {params}")
            
            upload_response = requests.post(
                upload_url,
                headers=headers,
                params=params,
                data=test_data,
                timeout=30
            )
            
            print(f"Upload status: {upload_response.status_code}")
            print(f"Upload response: {upload_response.text}")
            
            if upload_response.status_code in [200, 201]:
                result = upload_response.json()
                file_name = result.get('name', storage_path)
                encoded_name = requests.utils.quote(file_name, safe='')
                public_url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET_NAME}/o/{encoded_name}?alt=media"
                print(f"SUCCESS! Public URL: {public_url}")
                
                # Test if the URL is accessible
                test_response = requests.get(public_url)
                print(f"URL accessibility test: {test_response.status_code}")
                return True
            else:
                print(f"❌ Upload failed: {upload_response.status_code}")
                
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(f"Auth response: {auth_response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_firebase_upload()
    if success:
        print("\n✅ Firebase upload test PASSED")
    else:
        print("\n❌ Firebase upload test FAILED")