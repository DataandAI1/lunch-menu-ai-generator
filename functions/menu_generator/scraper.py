"""Web scraping functionality using Firecrawl"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from firecrawl import FirecrawlApp

from .models import MenuItem, NutritionalInfo


class MenuScraper:
    """Handles menu scraping with Firecrawl"""
    
    def __init__(self, api_key: str):
        self.app = FirecrawlApp(api_key=api_key)
    
    def get_week_dates(self, weeks_offset: int = 0) -> Dict[str, str]:
        """Get date range for a specific week"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        monday = monday + timedelta(weeks=weeks_offset)
        
        week_dates = {}
        for i in range(5):  # Monday to Friday
            day = monday + timedelta(days=i)
            day_name = day.strftime("%A")
            week_dates[day_name.lower()] = day.strftime("%B %d, %Y")
        
        return week_dates
    
    def scrape_with_nutrition(self, url: str) -> Optional[Dict]:
        """Scrape menu data including nutritional information"""
        
        # Define extraction schema
        schema = {
            "type": "object",
            "properties": {
                "monday": {
                    "type": "object",
                    "properties": {
                        "meal": {"type": "string", "description": "Lunch menu item for Monday"},
                        "calories": {"type": "integer", "description": "Calorie count"},
                        "allergens": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of allergens"
                        }
                    }
                },
                "tuesday": {
                    "type": "object",
                    "properties": {
                        "meal": {"type": "string"},
                        "calories": {"type": "integer"},
                        "allergens": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "wednesday": {
                    "type": "object",
                    "properties": {
                        "meal": {"type": "string"},
                        "calories": {"type": "integer"},
                        "allergens": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "thursday": {
                    "type": "object",
                    "properties": {
                        "meal": {"type": "string"},
                        "calories": {"type": "integer"},
                        "allergens": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "friday": {
                    "type": "object",
                    "properties": {
                        "meal": {"type": "string"},
                        "calories": {"type": "integer"},
                        "allergens": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }
        
        try:
            result = self.app.scrape_url(
                url,
                params={
                    'formats': ['extract'],
                    'extract': {
                        'schema': schema
                    }
                }
            )
            
            if 'extract' in result and result['extract']:
                return result['extract']
            
            # Fallback to basic scraping
            result = self.app.scrape_url(url, params={'formats': ['markdown']})
            if 'markdown' in result:
                # Return simple structure
                return self._parse_markdown_fallback(result['markdown'])
            
            return None
            
        except Exception as e:
            print(f"Error scraping: {e}")
            return None
    
    def _parse_markdown_fallback(self, markdown: str) -> Dict:
        """Simple fallback parser for markdown content"""
        # This is a simplified version - in production, you'd want more robust parsing
        days = {}
        lines = markdown.split('\n')
        
        current_day = None
        for line in lines:
            line = line.strip()
            if any(day in line.lower() for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                    if day in line.lower():
                        current_day = day
                        days[day] = {"meal": "", "calories": None, "allergens": []}
            elif current_day and line and not line.startswith('#'):
                if not days[current_day]["meal"]:
                    days[current_day]["meal"] = line
        
        return days
    
    def parse_menu_data(self, raw_data: Dict, weeks_offset: int = 0) -> Dict[str, MenuItem]:
        """Parse raw scraped data into MenuItem objects"""
        menu_items = {}
        week_dates = self.get_week_dates(weeks_offset)
        
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            if day in raw_data:
                day_data = raw_data[day]
                
                # Handle both simple string and complex object formats
                if isinstance(day_data, str):
                    meal_name = day_data
                    nutrition = None
                else:
                    meal_name = day_data.get('meal', 'No menu')
                    nutrition = NutritionalInfo(
                        calories=day_data.get('calories'),
                        allergens=day_data.get('allergens', [])
                    )
                
                menu_items[day] = MenuItem(
                    name=meal_name,
                    day=day,
                    date=week_dates[day],
                    nutrition=nutrition
                )
        
        return menu_items