// Default settings
const DEFAULT_SETTINGS = {
  defaultAction: 'both',
  maxEmails: 100,
  showConfirmation: true,
  theme: 'light'
};

// DOM elements
const actionTypeSelect = document.getElementById('action-type');
const maxEmailsInput = document.getElementById('max-emails');
const showConfirmationCheckbox = document.getElementById('show-confirmation');
const saveButton = document.getElementById('save-settings');
const manageAccountLink = document.getElementById('manage-account');
const helpLink = document.getElementById('help');

// Load saved settings
function loadSettings() {
  chrome.storage.sync.get(DEFAULT_SETTINGS, (settings) => {
    actionTypeSelect.value = settings.defaultAction;
    maxEmailsInput.value = settings.maxEmails;
    showConfirmationCheckbox.checked = settings.showConfirmation;
  });
}

// Save settings
function saveSettings() {
  const settings = {
    defaultAction: actionTypeSelect.value,
    maxEmails: parseInt(maxEmailsInput.value, 10) || 100,
    showConfirmation: showConfirmationCheckbox.checked,
    lastUpdated: new Date().toISOString()
  };

  chrome.storage.sync.set(settings, () => {
    // Show confirmation
    const status = document.createElement('div');
    status.textContent = 'Settings saved!';
    status.style.color = '#0f9d58';
    status.style.marginTop = '10px';
    saveButton.parentNode.appendChild(status);
    
    // Remove the status after 2 seconds
    setTimeout(() => {
      status.remove();
    }, 2000);
  });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', loadSettings);

saveButton.addEventListener('click', saveSettings);

// Allow saving with Enter key
document.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    saveSettings();
  }
});

// Handle help link
helpLink.addEventListener('click', (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: 'https://github.com/yourusername/unclut-ai#readme' });
});

// Handle account management
manageAccountLink.addEventListener('click', (e) => {
  e.preventDefault();
  chrome.runtime.openOptionsPage();
});
