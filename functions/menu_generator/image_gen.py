"""AI image generation using Google Gemini"""

import hashlib
import io
from typing import Optional
from datetime import datetime, timedelta

import google.generativeai as genai
from PIL import Image

from .models import MenuItem


class GeminiImageGenerator:
    """Handles AI image generation with Google Gemini and caching"""
    
    def __init__(self, api_key: str, storage_bucket, firestore_db):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.storage_bucket = storage_bucket
        self.db = firestore_db
        self.cache_max_age_days = 7
    
    def _get_cache_key(self, food_item: str, week_id: str) -> str:
        """Generate cache key for image"""
        content = f"{week_id}_{food_item.lower()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check if image exists in cache"""
        try:
            doc = self.db.collection('image_cache').document(cache_key).get()
            
            if doc.exists:
                data = doc.to_dict()
                cached_date = data['timestamp']
                age_days = (datetime.now() - cached_date).days
                
                if age_days <= self.cache_max_age_days:
                    # Check if blob still exists
                    blob = self.storage_bucket.blob(data['image_path'])
                    if blob.exists():
                        return blob.public_url
            
            return None
            
        except Exception as e:
            print(f"Cache check error: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, image_path: str, week_id: str, food_item: str):
        """Save image metadata to cache"""
        try:
            self.db.collection('image_cache').document(cache_key).set({
                'image_path': image_path,
                'week_id': week_id,
                'food_item': food_item,
                'timestamp': datetime.now()
            })
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def generate_image(self, food_item: str) -> Optional[Image.Image]:
        """Generate image using Gemini (placeholder for actual implementation)"""
        # Note: Actual Gemini image generation depends on available API features
        # This is a placeholder implementation
        
        try:
            prompt = (
                f"Generate a professional, appetizing food photography image of {food_item}. "
                f"The food should be served on a school lunch tray with bright, natural lighting. "
                f"Style: realistic, high-quality restaurant photography, vibrant colors, "
                f"sharp focus, delicious presentation. 8k quality."
            )
            
            # For now, create a placeholder image
            # In production, you would call Gemini's image generation API here
            img = Image.new('RGB', (512, 512), color='lightgray')
            
            # TODO: Replace with actual Gemini API call when available
            # response = self.model.generate_content([prompt])
            # Extract image from response
            
            return img
            
        except Exception as e:
            print(f"Image generation error: {e}")
            return None
    
    def generate_and_upload(self, menu_item: MenuItem, week_id: str) -> Optional[str]:
        """Generate image and upload to Firebase Storage with caching"""
        
        if not menu_item.name or menu_item.name.lower() in ['no school', 'holiday', 'skip', 'no menu']:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(menu_item.name, week_id)
        cached_url = self._check_cache(cache_key)
        
        if cached_url:
            print(f"Using cached image for {menu_item.name}")
            return cached_url
        
        # Generate new image
        image = self.generate_image(menu_item.name)
        
        if not image:
            return None
        
        # Upload to Storage
        try:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Upload to Firebase Storage
            blob_path = f"menu_images/{week_id}/{cache_key}.png"
            blob = self.storage_bucket.blob(blob_path)
            blob.upload_from_file(img_byte_arr, content_type='image/png')
            blob.make_public()
            
            # Save to cache
            self._save_to_cache(cache_key, blob_path, week_id, menu_item.name)
            
            return blob.public_url
            
        except Exception as e:
            print(f"Upload error: {e}")
            return None