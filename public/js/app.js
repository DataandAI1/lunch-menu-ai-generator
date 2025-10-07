/**
 * Lunch Menu Generator - Frontend Application
 * Handles UI interactions and API calls to Firebase Functions
 */

// Firebase Configuration
const firebaseConfig = {
  // These will be replaced with your actual Firebase config
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const storage = firebase.storage();

// State
let currentMenuData = null;
let currentWeekId = null;
let currentCalendarUrl = null;
let currentPdfUrl = null;

// DOM Elements
const elements = {
  // Step 1
  menuUrl: document.getElementById('menu-url'),
  weekOffset: document.getElementById('week-offset'),
  btnScrape: document.getElementById('btn-scrape'),
  
  // Step 2
  stepMenu: document.getElementById('step-menu'),
  menuWeekInfo: document.getElementById('menu-week-info'),
  menuPreview: document.getElementById('menu-preview'),
  btnEditMenu: document.getElementById('btn-edit-menu'),
  btnGenerate: document.getElementById('btn-generate'),
  
  // Step 3
  stepResult: document.getElementById('step-result'),
  calendarImage: document.getElementById('calendar-image'),
  btnDownloadPng: document.getElementById('btn-download-png'),
  btnDownloadPdf: document.getElementById('btn-download-pdf'),
  btnEmail: document.getElementById('btn-email'),
  btnNewMenu: document.getElementById('btn-new-menu'),
  
  // Loading & Modal
  loadingOverlay: document.getElementById('loading-overlay'),
  loadingText: document.getElementById('loading-text'),
  emailModal: document.getElementById('email-modal'),
  recipientEmail: document.getElementById('recipient-email'),
  btnSendEmail: document.getElementById('btn-send-email')
};

// Event Listeners
function initEventListeners() {
  elements.btnScrape.addEventListener('click', handleScrapeMenu);
  elements.btnGenerate.addEventListener('click', handleGenerateCalendar);
  elements.btnDownloadPng.addEventListener('click', handleDownloadPng);
  elements.btnDownloadPdf.addEventListener('click', handleDownloadPdf);
  elements.btnEmail.addEventListener('click', showEmailModal);
  elements.btnSendEmail.addEventListener('click', handleSendEmail);
  elements.btnNewMenu.addEventListener('click', resetApp);
}

// API Calls
async function callApi(endpoint, data) {
  try {
    const response = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Step 1: Scrape Menu
async function handleScrapeMenu() {
  const url = elements.menuUrl.value.trim();
  const weekOffset = parseInt(elements.weekOffset.value);
  
  if (!url) {
    showNotification('Please enter a valid URL', 'error');
    return;
  }
  
  showLoading('Scraping menu data...');
  
  try {
    const result = await callApi('scrape-menu', { url, week_offset: weekOffset });
    
    currentMenuData = result.menu_data;
    currentWeekId = result.week_id;
    
    displayMenuPreview(result.menu_data, result.week_info);
    showStep('menu');
    showNotification('Menu scraped successfully!', 'success');
    
  } catch (error) {
    showNotification(`Error: ${error.message}`, 'error');
  } finally {
    hideLoading();
  }
}

// Display Menu Preview
function displayMenuPreview(menuData, weekInfo) {
  elements.menuWeekInfo.textContent = `Week of ${weekInfo}`;
  elements.menuPreview.innerHTML = '';
  
  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
  
  days.forEach(day => {
    if (menuData[day]) {
      const item = menuData[day];
      const dayDiv = document.createElement('div');
      dayDiv.className = 'menu-day';
      
      let nutritionHtml = '';
      if (item.nutrition && item.nutrition.calories) {
        nutritionHtml = `
          <div class="menu-nutrition">
            <span>🔥 ${item.nutrition.calories} cal</span>
            ${item.nutrition.protein_g ? `<span>💪 ${item.nutrition.protein_g}g protein</span>` : ''}
          </div>
        `;
      }
      
      let allergensHtml = '';
      if (item.nutrition && item.nutrition.allergens && item.nutrition.allergens.length > 0) {
        allergensHtml = `
          <div class="menu-allergens">
            ⚠️ Contains: ${item.nutrition.allergens.join(', ')}
          </div>
        `;
      }
      
      dayDiv.innerHTML = `
        <div class="menu-day-header">
          <span class="menu-day-name">${day.charAt(0).toUpperCase() + day.slice(1)}</span>
          <span class="menu-day-date">${item.date}</span>
        </div>
        <div class="menu-item-name">🍽️ ${item.name}</div>
        ${nutritionHtml}
        ${allergensHtml}
      `;
      
      elements.menuPreview.appendChild(dayDiv);
    }
  });
}

// Step 2: Generate Calendar
async function handleGenerateCalendar() {
  if (!currentMenuData) {
    showNotification('No menu data available', 'error');
    return;
  }
  
  showLoading('Generating calendar with AI images...<br>This may take a few minutes.');
  
  try {
    const result = await callApi('generate-calendar', {
      menu_data: currentMenuData,
      week_id: currentWeekId
    });
    
    currentCalendarUrl = result.calendar_url;
    currentPdfUrl = result.pdf_url;
    
    elements.calendarImage.src = currentCalendarUrl;
    showStep('result');
    showNotification('Calendar generated successfully!', 'success');
    
  } catch (error) {
    showNotification(`Error: ${error.message}`, 'error');
  } finally {
    hideLoading();
  }
}

// Download PNG
function handleDownloadPng() {
  if (currentCalendarUrl) {
    const link = document.createElement('a');
    link.href = currentCalendarUrl;
    link.download = `lunch-menu-${currentWeekId}.png`;
    link.click();
    showNotification('Downloading PNG...', 'success');
  }
}

// Download PDF
async function handleDownloadPdf() {
  if (!currentPdfUrl) {
    showLoading('Generating PDF...');
    
    try {
      const result = await callApi('export-pdf', {
        menu_data: currentMenuData,
        week_id: currentWeekId
      });
      
      currentPdfUrl = result.pdf_url;
      
      const link = document.createElement('a');
      link.href = currentPdfUrl;
      link.download = `lunch-menu-${currentWeekId}.pdf`;
      link.click();
      showNotification('Downloading PDF...', 'success');
      
    } catch (error) {
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      hideLoading();
    }
  } else {
    const link = document.createElement('a');
    link.href = currentPdfUrl;
    link.download = `lunch-menu-${currentWeekId}.pdf`;
    link.click();
    showNotification('Downloading PDF...', 'success');
  }
}

// Email Modal
function showEmailModal() {
  elements.emailModal.classList.remove('hidden');
}

function closeEmailModal() {
  elements.emailModal.classList.add('hidden');
  elements.recipientEmail.value = '';
}

// Send Email
async function handleSendEmail() {
  const recipient = elements.recipientEmail.value.trim();
  
  if (!recipient) {
    showNotification('Please enter a recipient email', 'error');
    return;
  }
  
  if (!currentCalendarUrl) {
    showNotification('No calendar to send', 'error');
    return;
  }
  
  closeEmailModal();
  showLoading('Sending email...');
  
  try {
    await callApi('send-email', {
      recipient,
      calendar_url: currentCalendarUrl,
      pdf_url: currentPdfUrl,
      week_id: currentWeekId
    });
    
    showNotification('Email sent successfully!', 'success');
    
  } catch (error) {
    showNotification(`Error: ${error.message}`, 'error');
  } finally {
    hideLoading();
  }
}

// UI Helpers
function showStep(step) {
  document.querySelectorAll('.card').forEach(card => {
    if (card.id === `step-${step}`) {
      card.classList.remove('hidden');
      card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

function showLoading(text) {
  elements.loadingText.innerHTML = text;
  elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
  elements.loadingOverlay.classList.add('hidden');
}

function showNotification(message, type = 'info') {
  // Simple notification - can be enhanced with a toast library
  const colors = {
    success: '#27ae60',
    error: '#e74c3c',
    info: '#3498db'
  };
  
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${colors[type]};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function resetApp() {
  currentMenuData = null;
  currentWeekId = null;
  currentCalendarUrl = null;
  currentPdfUrl = null;
  
  elements.menuUrl.value = '';
  elements.weekOffset.value = '0';
  elements.stepMenu.classList.add('hidden');
  elements.stepResult.classList.add('hidden');
  
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showAbout() {
  alert('Lunch Menu AI Generator v2.0\n\nAn intelligent web app for creating beautiful school lunch menus with AI.\n\nFeatures:\n• AI-powered scraping\n• Gemini image generation\n• Nutrition tracking\n• PDF export\n• Email sharing');
}

function showPrivacy() {
  alert('Privacy Policy\n\nWe respect your privacy:\n• No personal data is stored\n• API keys are secure\n• Images cached temporarily\n• Emails sent securely\n\nFor more info, visit our GitHub.');
}

// CSS Animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  console.log('🍽️ Lunch Menu Generator loaded!');
});