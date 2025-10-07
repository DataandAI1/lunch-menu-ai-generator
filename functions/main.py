"""Firebase Cloud Functions for Lunch Menu Generator"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Request, jsonify
import functions_framework

from menu_generator.scraper import MenuScraper
from menu_generator.image_gen import GeminiImageGenerator
from menu_generator.calendar import CalendarCreator
from menu_generator.export import PDFExporter, EmailService
from menu_generator.models import MenuItem, NutritionalInfo

# Initialize Firebase Admin
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
storage_bucket = storage.bucket()

# Configuration from environment
CONFIG = {
    'firecrawl_api_key': os.getenv('FIRECRAWL_API_KEY'),
    'google_api_key': os.getenv('GOOGLE_API_KEY'),
    'email_address': os.getenv('EMAIL_ADDRESS'),
    'email_password': os.getenv('EMAIL_PASSWORD')
}


def get_week_identifier(weeks_offset: int = 0) -> str:
    """Get week identifier like '2024-W42'"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday = monday + timedelta(weeks=weeks_offset)
    return monday.strftime("%Y-W%U")


def cors_enabled(func):
    """Decorator to enable CORS for Cloud Functions"""
    def wrapper(request: Request):
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)
        
        # Set CORS headers for main request
        headers = {
            'Access-Control-Allow-Origin': '*'
        }
        
        try:
            result = func(request)
            return (result, 200, headers)
        except Exception as e:
            error_response = jsonify({'error': str(e)})
            return (error_response, 500, headers)
    
    return wrapper


@functions_framework.http
@cors_enabled
def scrape_menu(request: Request):
    """
    Scrape menu data from a URL
    
    Request body:
    {
        "url": "https://school.com/menu",
        "week_offset": 0
    }
    """
    data = request.get_json()
    url = data.get('url')
    week_offset = data.get('week_offset', 0)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Initialize scraper
        scraper = MenuScraper(CONFIG['firecrawl_api_key'])
        
        # Scrape menu
        week_id = get_week_identifier(week_offset)
        menu_data = scraper.scrape_with_nutrition(url)
        
        if not menu_data:
            return jsonify({'error': 'Failed to scrape menu'}), 500
        
        # Parse into MenuItem objects
        menu_items = scraper.parse_menu_data(menu_data, week_offset)
        
        # Cache in Firestore
        cache_ref = db.collection('menu_cache').document(f"{week_id}_{hash(url)}")
        cache_ref.set({
            'url': url,
            'week_id': week_id,
            'menu_data': {day: item.to_dict() for day, item in menu_items.items()},
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Get week info
        week_dates = scraper.get_week_dates(week_offset)
        monday_date = list(week_dates.values())[0]
        
        return jsonify({
            'menu_data': {day: item.to_dict() for day, item in menu_items.items()},
            'week_id': week_id,
            'week_info': monday_date
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@functions_framework.http
@cors_enabled
def generate_calendar(request: Request):
    """
    Generate calendar with AI-generated food images
    
    Request body:
    {
        "menu_data": {...},
        "week_id": "2024-W42"
    }
    """
    data = request.get_json()
    menu_data = data.get('menu_data')
    week_id = data.get('week_id')
    
    if not menu_data or not week_id:
        return jsonify({'error': 'menu_data and week_id are required'}), 400
    
    try:
        # Convert dict to MenuItem objects
        menu_items = {}
        for day, item_dict in menu_data.items():
            menu_items[day] = MenuItem.from_dict(item_dict)
        
        # Initialize image generator
        image_gen = GeminiImageGenerator(
            api_key=CONFIG['google_api_key'],
            storage_bucket=storage_bucket,
            firestore_db=db
        )
        
        # Generate images (with caching)
        for day, item in menu_items.items():
            image_url = image_gen.generate_and_upload(item, week_id)
            item.image_path = image_url
        
        # Create calendar
        calendar_creator = CalendarCreator(
            storage_bucket=storage_bucket
        )
        
        calendar_url = calendar_creator.create_and_upload(
            menu_items,
            week_id
        )
        
        # Store in Firestore
        menu_ref = db.collection('menus').document(week_id)
        menu_ref.set({
            'week_id': week_id,
            'menu_items': {day: item.to_dict() for day, item in menu_items.items()},
            'calendar_url': calendar_url,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            'calendar_url': calendar_url,
            'pdf_url': None  # Generated on demand
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@functions_framework.http
@cors_enabled
def export_pdf(request: Request):
    """
    Export menu as PDF
    
    Request body:
    {
        "menu_data": {...},
        "week_id": "2024-W42"
    }
    """
    data = request.get_json()
    menu_data = data.get('menu_data')
    week_id = data.get('week_id')
    
    if not menu_data or not week_id:
        return jsonify({'error': 'menu_data and week_id are required'}), 400
    
    try:
        # Convert to MenuItem objects
        menu_items = {}
        for day, item_dict in menu_data.items():
            menu_items[day] = MenuItem.from_dict(item_dict)
        
        # Generate PDF
        pdf_exporter = PDFExporter(
            storage_bucket=storage_bucket
        )
        
        pdf_url = pdf_exporter.create_and_upload(
            menu_items,
            week_id
        )
        
        return jsonify({
            'pdf_url': pdf_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@functions_framework.http
@cors_enabled
def send_email(request: Request):
    """
    Send menu via email
    
    Request body:
    {
        "recipient": "parent@email.com",
        "calendar_url": "...",
        "pdf_url": "...",
        "week_id": "2024-W42"
    }
    """
    data = request.get_json()
    recipient = data.get('recipient')
    calendar_url = data.get('calendar_url')
    pdf_url = data.get('pdf_url')
    week_id = data.get('week_id')
    
    if not recipient or not calendar_url:
        return jsonify({'error': 'recipient and calendar_url are required'}), 400
    
    try:
        # Send email
        email_service = EmailService(
            email_address=CONFIG['email_address'],
            email_password=CONFIG['email_password']
        )
        
        success = email_service.send_menu(
            recipient=recipient,
            calendar_url=calendar_url,
            pdf_url=pdf_url,
            week_id=week_id
        )
        
        if not success:
            return jsonify({'error': 'Failed to send email'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Email sent successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500