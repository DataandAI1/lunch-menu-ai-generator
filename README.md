# 🍽️ AI-Powered School Lunch Menu Generator

[![Firebase](https://img.shields.io/badge/Firebase-Ready-orange.svg)](https://firebase.google.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-4285F4.svg)](https://ai.google.dev/)

An intelligent web application that automatically scrapes school lunch menus, generates realistic food images using Google Gemini AI, tracks nutritional information, and creates beautiful weekly calendars.

## ✨ Features

- 🤖 **AI-Powered Scraping** - Automatically extracts menu data using Firecrawl
- 🎨 **Gemini Image Generation** - Creates photorealistic food images
- 🥗 **Nutrition Tracking** - Displays calories, protein, and allergens
- 📅 **Multi-Week View** - Browse past, current, and future weeks
- ♻️ **Smart Caching** - Avoids regenerating images (saves time & API costs)
- 📄 **PDF Export** - Generate printable weekly menus
- 📧 **Email Sharing** - Share menus directly via email
- 🔒 **Firebase Backend** - Secure, scalable cloud infrastructure

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Firebase CLI (`npm install -g firebase-tools`)
- Google Cloud Project with Firebase enabled
- API Keys:
  - [Firecrawl API Key](https://www.firecrawl.dev)
  - [Google AI Studio API Key](https://aistudio.google.com/apikey)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DataandAI1/lunch-menu-ai-generator.git
   cd lunch-menu-ai-generator
   ```

2. **Install dependencies**
   ```bash
   # Frontend dependencies
   npm install
   
   # Backend dependencies
   cd functions
   pip install -r requirements.txt
   cd ..
   ```

3. **Configure Firebase**
   ```bash
   firebase login
   firebase init
   ```

4. **Set up environment variables**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env with your API keys
   nano .env
   
   # Set Firebase environment config
   firebase functions:config:set \
     firecrawl.api_key="your_key" \
     google.api_key="your_key" \
     email.address="your_email" \
     email.password="your_app_password"
   ```

5. **Deploy to Firebase**
   ```bash
   firebase deploy
   ```

## 📖 Detailed Setup Guide

See [SETUP.md](SETUP.md) for comprehensive setup instructions including:
- Firebase project creation
- API key configuration
- Local development setup
- Deployment strategies

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
│  (React UI) │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Firebase        │
│ Hosting         │
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│ Cloud Functions (Python)    │
├─────────────────────────────┤
│ • Menu Scraper (Firecrawl)  │
│ • Image Gen (Gemini)        │
│ • PDF Generator             │
│ • Email Service             │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Firebase Services           │
├─────────────────────────────┤
│ • Firestore (Menu Cache)    │
│ • Storage (Images)          │
│ • Authentication (Optional) │
└─────────────────────────────┘
```

## 🎯 API Endpoints

### `POST /api/scrape-menu`
Scrapes menu data from a URL
```json
{
  "url": "https://school.com/lunch-menu",
  "week_offset": 0
}
```

### `POST /api/generate-calendar`
Generates calendar with images
```json
{
  "menu_data": {...},
  "week_id": "2024-W42"
}
```

### `POST /api/export-pdf`
Exports menu as PDF
```json
{
  "menu_items": [...],
  "week_id": "2024-W42"
}
```

### `POST /api/send-email`
Shares menu via email
```json
{
  "recipient": "parent@email.com",
  "calendar_url": "...",
  "pdf_url": "..."
}
```

## 🛠️ Development

### Local Development

```bash
# Start Firebase emulators
firebase emulators:start

# In another terminal, start the frontend
npm run dev

# Visit http://localhost:5000
```

### Running Tests

```bash
# Frontend tests
npm test

# Backend tests
cd functions
pytest
```

## 📁 Project Structure

```
lunch-menu-ai-generator/
├── public/                 # Frontend static files
│   ├── index.html         # Main HTML
│   ├── css/
│   │   └── styles.css     # Styles
│   └── js/
│       └── app.js         # Frontend logic
├── functions/             # Firebase Cloud Functions
│   ├── main.py           # Entry point
│   ├── requirements.txt  # Python dependencies
│   └── menu_generator/   # Core logic
│       ├── scraper.py    # Firecrawl integration
│       ├── image_gen.py  # Gemini integration
│       ├── calendar.py   # Calendar creation
│       ├── export.py     # PDF/Email export
│       └── models.py     # Data models
├── firebase.json         # Firebase configuration
├── .firebaserc          # Firebase project settings
├── firestore.rules      # Database security rules
├── storage.rules        # Storage security rules
└── package.json         # Node.js dependencies
```

## 🔐 Security

- API keys stored in Firebase environment config
- Firestore security rules restrict data access
- CORS properly configured
- Input validation on all endpoints
- Rate limiting enabled

## 💰 Cost Considerations

- **Firecrawl**: Free tier includes 500 requests/month
- **Google Gemini**: Free tier includes 60 requests/minute
- **Firebase**: Free Spark plan for small usage
- **Estimated**: ~$0-5/month for typical school use

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- [Firecrawl](https://www.firecrawl.dev) - Web scraping API
- [Google Gemini](https://ai.google.dev/) - AI image generation
- [Firebase](https://firebase.google.com/) - Backend infrastructure

## 📧 Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/DataandAI1/lunch-menu-ai-generator/issues)
- Check the [documentation](https://github.com/DataandAI1/lunch-menu-ai-generator/wiki)

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Recipe suggestions
- [ ] Dietary preference filtering
- [ ] Parent feedback system
- [ ] Admin dashboard for schools

---

Made with ❤️ for schools and parents