"""Firebase Cloud Functions for Lunch Menu Generator"""

import os
from datetime import datetime, timedelta
from typing import Dict

import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Request, jsonify, make_response, Response
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
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        if request.method == 'OPTIONS':
            response = make_response('', 204)
            response.headers.update(cors_headers)
            return response

        try:
            result = func(request)
        except Exception as exc:  # pragma: no cover - defensive programming
            result = (jsonify({'error': str(exc)}), 500)

        extra_headers: Dict[str, str] = {}

        if isinstance(result, tuple):
            body = result[0]
            status = result[1] if len(result) > 1 else 200
            extra_headers = result[2] if len(result) > 2 else {}

            if isinstance(body, Response):
                response = body
                response.status_code = status
            else:
                response = make_response(body, status)
        else:
            response = result if isinstance(result, Response) else make_response(result, 200)

        response.headers.update(cors_headers)
        response.headers.update(extra_headers)
        return response

    return wrapper


@functions_framework.http
@cors_enabled
def scrape_menu(request: Request):
    """Scrape menu data from a URL and return today's menu item."""

    data = request.get_json(silent=True) or {}
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Determine today's weekday identifier
    today = datetime.now()
    today_key = today.strftime('%A').lower()

    try:
        scraper = MenuScraper(CONFIG['firecrawl_api_key'])
        menu_data = scraper.scrape_with_nutrition(url)

        if not menu_data:
            return jsonify({'error': 'Failed to scrape menu'}), 502

        menu_items = scraper.parse_menu_data(menu_data, 0)
        today_item = menu_items.get(today_key)

        if not today_item:
            error_message = f'No menu information found for {today.strftime("%A")}'
            return jsonify({'error': error_message}), 404

        # Cache today's result for quick access later
        cache_ref = db.collection('menu_cache').document(f"{today_key}_{today.strftime('%Y%m%d')}_{hash(url)}")
        cache_ref.set({
            'url': url,
            'day': today_key,
            'date': today_item.date,
            'menu_item': today_item.to_dict(),
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            'menu_item': today_item.to_dict(),
            'day': today_key,
            'date': today_item.date
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
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
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