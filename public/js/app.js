/**
 * Lunch Menu Finder - Frontend Application
 * Simplified UI for retrieving today's lunch menu.
 */

// DOM Elements
const elements = {
  menuUrl: document.getElementById('menu-url'),
  btnSearch: document.getElementById('btn-search'),
  resultCard: document.getElementById('today-menu'),
  menuDate: document.getElementById('menu-date'),
  menuDetails: document.getElementById('menu-details'),
  todayLabel: document.getElementById('today-label'),
  loadingOverlay: document.getElementById('loading-overlay'),
  loadingText: document.getElementById('loading-text')
};

function initEventListeners() {
  if (elements.btnSearch) {
    elements.btnSearch.addEventListener('click', handleFindTodayMenu);
  }

  if (elements.menuUrl) {
    elements.menuUrl.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        handleFindTodayMenu();
      }
    });
  }
}

async function callApi(endpoint, data) {
  try {
    const response = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json'
      },
      body: JSON.stringify(data)
    });

    const responseText = await response.text();
    let jsonData = null;

    if (responseText) {
      try {
        jsonData = JSON.parse(responseText);
      } catch (parseError) {
        console.error('JSON parse error:', parseError, responseText);
        throw new Error('The server returned invalid JSON. Please try again later.');
      }
    }

    if (!response.ok) {
      const errorMessage = jsonData && (jsonData.error || jsonData.message);
      throw new Error(errorMessage || `Request failed with status ${response.status}`);
    }

    if (jsonData === null) {
      throw new Error('Received an empty response from the server.');
    }

    return jsonData;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

async function handleFindTodayMenu() {
  const url = elements.menuUrl ? elements.menuUrl.value.trim() : '';

  if (!url) {
    showNotification('Please enter a valid URL', 'error');
    return;
  }

  hideResult();
  showLoading("Fetching today's menu...");

  try {
    const result = await callApi('scrape-menu', { url });
    displayTodayMenu(result);
    showNotification("Today's menu loaded!", 'success');
  } catch (error) {
    showNotification(`Error: ${error.message}`, 'error');
  } finally {
    hideLoading();
  }
}

function displayTodayMenu(data) {
  const menuItem = data && data.menu_item;

  if (!menuItem) {
    showNotification('No lunch information found for today.', 'error');
    return;
  }

  const dayName = data.day ? capitalize(data.day) : capitalize(menuItem.day || '');
  const dateText = data.date || menuItem.date || '';

  if (elements.menuDate) {
    const formatted = [dateText, dayName].filter(Boolean).join(' • ');
    elements.menuDate.textContent = formatted || 'Today';
  }

  if (elements.menuDetails) {
    elements.menuDetails.innerHTML = '';
    elements.menuDetails.appendChild(renderMenuItem(menuItem));
  }

  if (elements.resultCard) {
    elements.resultCard.classList.remove('hidden');
    elements.resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function renderMenuItem(menuItem) {
  const container = document.createElement('div');
  container.className = 'menu-day';

  const nutrition = menuItem.nutrition || {};
  const nutritionParts = [];

  if (nutrition.calories) {
    nutritionParts.push(`🔥 ${nutrition.calories} cal`);
  }
  if (nutrition.protein_g) {
    nutritionParts.push(`💪 ${nutrition.protein_g}g protein`);
  }

  const nutritionHtml = nutritionParts.length
    ? `<div class="menu-nutrition">${nutritionParts.map(part => `<span>${part}</span>`).join('')}</div>`
    : '';

  const allergens = Array.isArray(nutrition.allergens) ? nutrition.allergens : [];
  const allergensHtml = allergens.length
    ? `<div class="menu-allergens">⚠️ Contains: ${allergens.join(', ')}</div>`
    : '';

  container.innerHTML = `
    <div class="menu-day-header">
      <span class="menu-day-name">${capitalize(menuItem.day || '')}</span>
      <span class="menu-day-date">${menuItem.date || ''}</span>
    </div>
    <div class="menu-item-name">🍽️ ${menuItem.name || 'No menu available'}</div>
    ${nutritionHtml}
    ${allergensHtml}
  `;

  return container;
}

function hideResult() {
  if (elements.resultCard) {
    elements.resultCard.classList.add('hidden');
  }
}

function showLoading(text) {
  if (elements.loadingText) {
    elements.loadingText.innerHTML = text;
  }
  if (elements.loadingOverlay) {
    elements.loadingOverlay.classList.remove('hidden');
  }
}

function hideLoading() {
  if (elements.loadingOverlay) {
    elements.loadingOverlay.classList.add('hidden');
  }
}

function showNotification(message, type = 'info') {
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
    background: ${colors[type] || colors.info};
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

function capitalize(text) {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function showAbout() {
  alert('Lunch Menu Finder\n\nQuickly look up today\'s school lunch using your menu link.');
}

function showPrivacy() {
  alert('Privacy Notice\n\nNo personal data is stored. Menu links are used only to look up today\'s lunch.');
}

// CSS Animations (unchanged)
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
if (elements.todayLabel) {
  const today = new Date();
  elements.todayLabel.textContent = `Today is ${today.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  })}`;
}

document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  console.log('🍽️ Lunch Menu Finder loaded!');
});

// Expose helper functions for footer links
window.showAbout = showAbout;
window.showPrivacy = showPrivacy;
