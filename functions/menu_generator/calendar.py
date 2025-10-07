"""Calendar creation with PIL"""

import io
from typing import Dict
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import requests

from .models import MenuItem


class CalendarCreator:
    """Creates weekly menu calendar images"""
    
    # Configuration
    CELL_WIDTH = 320
    CELL_HEIGHT = 500
    PADDING = 25
    HEADER_HEIGHT = 70
    IMAGE_HEIGHT = 200
    NUTRITION_HEIGHT = 80
    
    # Colors
    BG_COLOR = "#F5F5F0"
    TEXT_COLOR = "#2C3E50"
    BORDER_COLOR = "#34495E"
    HEADER_BG = "#3498DB"
    NUTRITION_BG = "#ECF0F1"
    ALLERGEN_WARNING = "#E74C3C"
    
    def __init__(self, storage_bucket):
        self.storage_bucket = storage_bucket
    
    def _load_default_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load default font"""
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()
    
    def _download_image(self, url: str) -> Image.Image:
        """Download image from URL"""
        try:
            response = requests.get(url)
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Error downloading image: {e}")
            # Return placeholder
            return Image.new('RGB', (200, 200), color='lightgray')
    
    def create_calendar(self, menu_items: Dict[str, MenuItem]) -> Image.Image:
        """Create the calendar image"""
        
        days = list(menu_items.keys())
        num_days = len(days)
        
        # Calculate dimensions
        total_width = (self.CELL_WIDTH * num_days) + (self.PADDING * (num_days + 1))
        total_height = self.CELL_HEIGHT + (self.PADDING * 2) + self.HEADER_HEIGHT
        
        # Create canvas
        calendar = Image.new("RGB", (total_width, total_height), self.BG_COLOR)
        draw = ImageDraw.Draw(calendar)
        
        # Load fonts
        day_font = self._load_default_font(28)
        date_font = self._load_default_font(12)
        menu_font = self._load_default_font(15)
        nutrition_font = self._load_default_font(10)
        
        # Draw each day cell
        for i, day in enumerate(days):
            item = menu_items[day]
            
            # Calculate position
            x = self.PADDING + i * (self.CELL_WIDTH + self.PADDING)
            y = self.PADDING
            
            # Draw cell
            cell_rect = [x, y, x + self.CELL_WIDTH, y + self.HEADER_HEIGHT + self.CELL_HEIGHT]
            draw.rectangle(cell_rect, fill="white", outline=self.BORDER_COLOR, width=3)
            
            # Header
            header_rect = [x, y, x + self.CELL_WIDTH, y + self.HEADER_HEIGHT]
            draw.rectangle(header_rect, fill=self.HEADER_BG)
            
            # Day name
            day_text = item.day.capitalize()
            day_bbox = draw.textbbox((0, 0), day_text, font=day_font)
            day_width = day_bbox[2] - day_bbox[0]
            draw.text((x + (self.CELL_WIDTH - day_width) // 2, y + 15), day_text, font=day_font, fill="white")
            
            # Date
            date_bbox = draw.textbbox((0, 0), item.date, font=date_font)
            date_width = date_bbox[2] - date_bbox[0]
            draw.text((x + (self.CELL_WIDTH - date_width) // 2, y + 48), item.date, font=date_font, fill="white")
            
            # Food image
            image_y = y + self.HEADER_HEIGHT + 10
            if item.image_path:
                try:
                    food_image = self._download_image(item.image_path)
                    food_image.thumbnail((self.CELL_WIDTH - 20, self.IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                    img_x = x + (self.CELL_WIDTH - food_image.width) // 2
                    calendar.paste(food_image, (img_x, image_y))
                    text_y = image_y + food_image.height + 10
                except:
                    text_y = image_y + 10
            else:
                text_y = image_y + 10
            
            # Menu name
            max_chars = 24
            words = item.name.split()
            lines = []
            current_line = ""
            
            for word in words:
                test = current_line + (" " if current_line else "") + word
                if len(test) <= max_chars:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines[:2]:
                line_bbox = draw.textbbox((0, 0), line, font=menu_font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text((x + (self.CELL_WIDTH - line_width) // 2, text_y), line, font=menu_font, fill=self.TEXT_COLOR)
                text_y += 20
            
            # Nutrition section
            nutrition_y = y + self.HEADER_HEIGHT + self.IMAGE_HEIGHT + 80
            nutrition_rect = [x + 5, nutrition_y, x + self.CELL_WIDTH - 5, nutrition_y + self.NUTRITION_HEIGHT]
            draw.rectangle(nutrition_rect, fill=self.NUTRITION_BG, outline=self.BORDER_COLOR, width=1)
            
            if item.nutrition and item.nutrition.has_data:
                nut_y = nutrition_y + 8
                
                if item.nutrition.calories:
                    draw.text((x + 10, nut_y), f"🔥 {item.nutrition.calories} cal", font=nutrition_font, fill=self.TEXT_COLOR)
                    nut_y += 15
                
                if item.nutrition.protein_g:
                    draw.text((x + 10, nut_y), f"💪 {item.nutrition.protein_g}g protein", font=nutrition_font, fill=self.TEXT_COLOR)
                    nut_y += 15
                
                if item.nutrition.allergens:
                    allergen_text = "⚠️  " + ", ".join(item.nutrition.allergens[:2])
                    draw.text((x + 10, nut_y), allergen_text, font=nutrition_font, fill=self.ALLERGEN_WARNING)
            else:
                draw.text((x + 10, nutrition_y + 30), "No nutrition data", font=nutrition_font, fill="#999")
        
        return calendar
    
    def create_and_upload(self, menu_items: Dict[str, MenuItem], week_id: str) -> str:
        """Create calendar and upload to Firebase Storage"""
        
        # Create calendar
        calendar = self.create_calendar(menu_items)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        calendar.save(img_byte_arr, format='PNG', quality=95, optimize=True)
        img_byte_arr.seek(0)
        
        # Upload to Storage
        blob_path = f"menu_calendars/{week_id}/calendar.png"
        blob = self.storage_bucket.blob(blob_path)
        blob.upload_from_file(img_byte_arr, content_type='image/png')
        blob.make_public()
        
        return blob.public_url