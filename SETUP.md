# 🚀 Complete Setup Guide

## Prerequisites

Before you begin, ensure you have:

- **Node.js** 18+ and npm installed
- **Python** 3.11+ installed
- **Firebase CLI** installed: `npm install -g firebase-tools`
- A **Google Cloud Project** with billing enabled
- **Git** installed

## Step 1: Firebase Project Setup

### 1.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name (e.g., `lunch-menu-generator`)
4. Enable Google Analytics (optional)
5. Click "Create project"

### 1.2 Enable Firebase Services

In your Firebase project:

1. **Firestore Database**:
   - Go to Firestore Database
   - Click "Create database"
   - Start in production mode
   - Choose a location close to your users

2. **Firebase Storage**:
   - Go to Storage
   - Click "Get started"
   - Start in production mode

3. **Firebase Functions**:
   - Automatically enabled when you deploy

### 1.3 Get Firebase Configuration

1. Go to Project Settings (gear icon)
2. Scroll to "Your apps"
3. Click the web icon `</>`
4. Register app (name: "Lunch Menu Web")
5. Copy the `firebaseConfig` object
6. Update `public/js/app.js` with your config

## Step 2: Get API Keys

### 2.1 Firecrawl API Key

1. Go to [Firecrawl.dev](https://www.firecrawl.dev)
2. Sign up for a free account
3. Navigate to API Keys
4. Copy your API key
5. Free tier: 500 requests/month

### 2.2 Google AI Studio API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Get API Key"
3. Create a new API key or use existing
4. Copy the API key
5. Free tier: 60 requests/minute

### 2.3 Email Configuration (Optional)

For Gmail:

1. Enable 2-factor authentication
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification
   - App passwords
   - Generate password for "Mail"
   - Copy the 16-character password

## Step 3: Clone and Setup

### 3.1 Clone Repository

```bash
git clone https://github.com/DataandAI1/lunch-menu-ai-generator.git
cd lunch-menu-ai-generator
```

### 3.2 Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies for Functions
cd functions
pip install -r requirements.txt
cd ..
```

### 3.3 Configure Firebase

```bash
# Login to Firebase
firebase login

# Initialize Firebase project
firebase use --add
# Select your project from the list
# Give it an alias (e.g., "default")
```

Update `.firebaserc` with your project ID:

```json
{
  "projects": {
    "default": "your-project-id"
  }
}
```

### 3.4 Set Environment Variables

Set Firebase Functions configuration:

```bash
firebase functions:config:set \
  firecrawl.api_key="your_firecrawl_key" \
  google.api_key="your_google_ai_key" \
  email.address="your_email@gmail.com" \
  email.password="your_app_password"
```

Verify configuration:

```bash
firebase functions:config:get
```

## Step 4: Local Development

### 4.1 Start Firebase Emulators

```bash
firebase emulators:start
```

This starts:
- **Hosting** on http://localhost:5000
- **Functions** on http://localhost:5001
- **Firestore** on http://localhost:8080
- **Storage** on http://localhost:9199
- **Emulator UI** on http://localhost:4000

### 4.2 Test Locally

1. Open http://localhost:5000 in your browser
2. Enter a test menu URL
3. Test the scraping and generation
4. Check the Emulator UI for logs

## Step 5: Deploy to Production

### 5.1 Deploy Everything

```bash
# Deploy all Firebase services
firebase deploy
```

Or deploy individually:

```bash
# Deploy only hosting
firebase deploy --only hosting

# Deploy only functions
firebase deploy --only functions

# Deploy only Firestore rules
firebase deploy --only firestore:rules

# Deploy only Storage rules
firebase deploy --only storage:rules
```

### 5.2 Get Your Live URL

After deployment:

```
✔  Deploy complete!

Hosting URL: https://your-project.web.app
```

Your app is now live!

## Step 6: Testing

### 6.1 Test Web App

1. Visit your live URL
2. Enter a school menu URL (examples below)
3. Test all features:
   - Menu scraping
   - Image generation
   - PDF export
   - Email sending

### 6.2 Test Menu URLs

Try these example school lunch menu sites:

- https://www.exampleschool.edu/nutrition/menu
- https://www.schoolnutrition.org/sample-menus

### 6.3 Monitor Functions

```bash
# View function logs
firebase functions:log

# Follow logs in real-time
firebase functions:log --only scrape_menu
```

## Step 7: Monitoring & Maintenance

### 7.1 Firebase Console

Monitor in [Firebase Console](https://console.firebase.google.com/):

- **Functions**: Check execution logs, errors, usage
- **Firestore**: View cached data, set up indexes
- **Storage**: Monitor storage usage, manage files
- **Hosting**: Check bandwidth usage

### 7.2 Set Up Alerts

1. Go to Cloud Console → Monitoring
2. Create alerts for:
   - Function errors > 10/hour
   - Storage usage > 80%
   - Function execution time > 60s

### 7.3 Cost Management

**Firebase Spark Plan (Free)**:
- Hosting: 10GB storage, 360MB/day transfer
- Functions: 125K invocations/month, 40K compute seconds
- Firestore: 1GB storage, 50K reads/day
- Storage: 5GB

**Upgrade to Blaze (Pay-as-you-go)**:
- Required for: External API calls (Firecrawl, Gemini)
- Set budget alerts in Google Cloud Console

## Step 8: Customization

### 8.1 Branding

Update colors in `public/css/styles.css`:

```css
:root {
  --primary: #3498db;  /* Change to your school colors */
  --header-bg: #2c3e50;
}
```

### 8.2 Calendar Layout

Modify calendar settings in `functions/menu_generator/calendar.py`:

```python
CELL_WIDTH = 320  # Adjust cell dimensions
CELL_HEIGHT = 500
```

### 8.3 Email Template

Customize email in `functions/menu_generator/export.py`:

```python
body = f"""
<html>
  <!-- Your custom HTML template -->
</html>
"""
```

## Troubleshooting

### Common Issues

**1. Firebase Deploy Fails**
```bash
# Solution: Ensure you're logged in
firebase logout
firebase login
```

**2. Functions Timeout**
```bash
# Solution: Increase timeout in firebase.json
"functions": {
  "runtime": "python311",
  "timeout": "120s"  # Increase from default 60s
}
```

**3. CORS Errors**
- Check that `cors_enabled` decorator is applied to all functions
- Verify Firebase Hosting rewrites in `firebase.json`

**4. Image Generation Fails**
- Verify Google API key has Gemini access
- Check API quota limits
- Review function logs for specific errors

**5. Email Not Sending**
- Verify Gmail App Password (not regular password)
- Check that less secure app access is enabled
- Review SMTP logs in function output

### Getting Help

- **GitHub Issues**: https://github.com/DataandAI1/lunch-menu-ai-generator/issues
- **Firebase Support**: https://firebase.google.com/support
- **Documentation**: Check the README and code comments

## Security Best Practices

1. **Never commit API keys** to Git
2. **Use Firebase security rules** (already configured)
3. **Enable Firebase App Check** for production
4. **Set up monitoring alerts**
5. **Regularly update dependencies**

## Next Steps

✅ App is deployed and running!  
✅ Share your live URL with users  
✅ Monitor usage and costs  
✅ Collect feedback and iterate  

---

**Need help?** Open an issue on [GitHub](https://github.com/DataandAI1/lunch-menu-ai-generator/issues) or check the [documentation](https://firebase.google.com/docs).