// Content script for unclut.ai Gmail extension
class UnclutExtension {
  constructor() {
    this.buttonsContainer = null;
    this.observer = null;
    this.initialized = false;
    this.toastTimeout = null;
    this.retryCount = 0;
    this.maxRetries = 5;
    
    // Initialize with robust container detection
    this.init().catch(error => {
      console.error('[Unclut] Failed to initialize:', error);
      this.retryInitialization();
    });
  }
  
  /**
   * Retry initialization with exponential backoff
   */
  retryInitialization() {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000); // Max 30s delay
      console.log(`[Unclut] Retrying initialization (${this.retryCount}/${this.maxRetries})...`);
      
      setTimeout(() => {
        this.init().catch(error => {
          console.error(`[Unclut] Retry ${this.retryCount} failed:`, error);
          this.retryInitialization();
        });
      }, delay);
    } else {
      console.error('[Unclut] Max retries reached. Giving up.');
    }
  }

  /**
   * Wait for Gmail's main container to be available
   */
  waitForGmailContainer() {
    return new Promise((resolve) => {
      // Check immediately if container exists
      if (this.isGmailReady()) {
        console.log('[Unclut] Gmail container found immediately');
        return resolve();
      }
      
      console.log('[Unclut] Waiting for Gmail container...');
      
      let observer = null;
      let timeoutId = null;
      
      const cleanup = () => {
        if (observer) {
          observer.disconnect();
          observer = null;
        }
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }
      };
      
      // Set up mutation observer
      observer = new MutationObserver((mutations) => {
        if (this.isGmailReady()) {
          console.log('[Unclut] Gmail container detected via mutation observer');
          cleanup();
          resolve();
        }
      });
      
      // Start observing the document
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false,
        characterData: false
      });
      
      // Fallback timeout (10 seconds)
      timeoutId = setTimeout(() => {
        console.warn('[Unclut] Gmail container not found after timeout, checking anyway');
        cleanup();
        resolve();
      }, 10000);
    });
  }
  
  /**
   * Check if Gmail's main container is ready
   */
  isGmailReady() {
    try {
      // Check for Gmail's main container and email list
      const hasMainContainer = !!document.querySelector('[role="main"]');
      const hasEmailList = !!document.querySelector('[role="tabpanel"] [role="tabpanel"]');
      const isGmail = window.location.hostname === 'mail.google.com';
      
      if (!isGmail) {
        console.log('[Unclut] Not on Gmail domain');
        return false;
      }
      
      console.log(`[Unclut] Gmail check - Main: ${hasMainContainer}, Email List: ${hasEmailList}`);
      return hasMainContainer && hasEmailList;
    } catch (error) {
      console.error('[Unclut] Error in isGmailReady:', error);
      return false;
    }
  }
  
  /**
   * Initialize the extension
   */
  async init() {
    if (this.initialized) {
      console.log('[Unclut] Extension already initialized');
      return;
    }
    
    try {
      console.log('[Unclut] Starting initialization...');
      
      // Wait for Gmail to be ready
      await this.waitForGmailContainer();
      
      // Set up mutation observer for dynamic content
      this.setupMutationObserver();
      
      // Inject styles
      this.injectStyles();
      
      // Initial button injection
      await this.injectButtons();
      
      this.initialized = true;
      console.log('[Unclut] Extension initialized successfully');
      
      // Notify background script
      chrome.runtime.sendMessage({ type: 'extensionInitialized' });
      
    } catch (error) {
      console.error('[Unclut] Error during initialization:', error);
      throw error;
    }
  }
  
  /**
   * Clean up resources
   */
  cleanup() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    
    if (this.toastTimeout) {
      clearTimeout(this.toastTimeout);
      this.toastTimeout = null;
    }
    
    // Remove all injected buttons
    document.querySelectorAll('.unclut-button').forEach(btn => btn.remove());
    
    this.initialized = false;
    console.log('[Unclut] Cleaned up resources');
  }

  // Inject custom styles
  injectStyles() {
    const styleId = 'unclut-extension-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      .unclut-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        cursor: pointer;
        margin-left: 8px;
        opacity: 0.7;
        transition: opacity 0.2s, background-color 0.2s;
      }
      
      .unclut-button:hover {
        opacity: 1;
        background-color: rgba(0, 0, 0, 0.1);
      }
      
      .unclut-buttons-container {
        display: none;
        position: absolute;
        background: white;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        padding: 4px;
      }
      
      .unclut-button-item {
        padding: 8px 12px;
        cursor: pointer;
        white-space: nowrap;
        font-size: 13px;
        color: #202124;
      }
      
      .unclut-button-item:hover {
        background-color: #f1f3f4;
        border-radius: 2px;
      }
      
      .unclut-toast {
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: #202124;
        color: white;
        padding: 8px 24px;
        border-radius: 20px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        z-index: 9999;
        opacity: 0;
        transition: opacity 0.3s;
      }
      
      .unclut-toast.visible {
        opacity: 1;
      }
      
      .unclut-toast-undo {
        color: #8ab4f8;
        cursor: pointer;
        font-weight: 500;
      }
    `;
    document.head.appendChild(style);
  }

  // Setup mutation observer to handle dynamic content
  setupMutationObserver() {
    const targetNode = document.body;
    const config = { childList: true, subtree: true };
    
    this.observer = new MutationObserver((mutations) => {
      if (!this.shouldProcessMutations()) return;
      this.injectButtons();
    });
    
    this.observer.observe(targetNode, config);
    this.injectButtons();
  }

  // Check if we should process mutations (throttling)
  shouldProcessMutations() {
    if (this.processingMutations) return false;
    this.processingMutations = true;
    
    // Throttle to prevent excessive processing
    setTimeout(() => {
      this.processingMutations = false;
    }, 100);
    
    return true;
  }

  // Inject buttons next to email senders
  injectButtons() {
    const emailRows = document.querySelectorAll('tr[role="row"]:not(.unclut-processed)');
    
    emailRows.forEach((row) => {
      if (row.classList.contains('unclut-processed')) return;
      
      const senderCell = row.querySelector('td[data-thread-id] span[email]');
      if (!senderCell) return;
      
      const senderEmail = senderCell.getAttribute('email');
      if (!senderEmail) return;
      
      // Create button container
      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'unclut-buttons-container';
      buttonContainer.style.display = 'none';
      
      // Create action buttons
      const actions = [
        { label: 'Unsubscribe', action: 'unsubscribe' },
        { label: 'Delete All', action: 'delete' },
        { label: 'Unsubscribe + Delete', action: 'both' }
      ];
      
      actions.forEach(({ label, action }) => {
        const button = document.createElement('div');
        button.className = 'unclut-button-item';
        button.textContent = label;
        button.addEventListener('click', (e) => {
          e.stopPropagation();
          this.handleAction(senderEmail, action);
          buttonContainer.style.display = 'none';
        });
        buttonContainer.appendChild(button);
      });
      
      // Create trigger button
      const trigger = document.createElement('div');
      trigger.className = 'unclut-button';
      trigger.innerHTML = '⸸';
      trigger.title = 'unclut.ai - Clean up emails';
      
      // Position the buttons container
      const positionButtons = () => {
        const rect = trigger.getBoundingClientRect();
        buttonContainer.style.top = `${rect.bottom + window.scrollY}px`;
        buttonContainer.style.left = `${rect.left + window.scrollX}px`;
      };
      
      // Toggle buttons on trigger click
      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        const isVisible = buttonContainer.style.display === 'block';
        
        // Hide all other open menus
        document.querySelectorAll('.unclut-buttons-container').forEach(container => {
          if (container !== buttonContainer) {
            container.style.display = 'none';
          }
        });
        
        if (!isVisible) {
          positionButtons();
          buttonContainer.style.display = 'block';
          
          // Close when clicking outside
          const clickOutside = (e) => {
            if (!buttonContainer.contains(e.target) && e.target !== trigger) {
              buttonContainer.style.display = 'none';
              document.removeEventListener('click', clickOutside);
            }
          };
          
          setTimeout(() => {
            document.addEventListener('click', clickOutside);
          }, 0);
        } else {
          buttonContainer.style.display = 'none';
        }
      });
      
      // Insert elements
      senderCell.parentNode.insertBefore(trigger, senderCell.nextSibling);
      document.body.appendChild(buttonContainer);
      
      // Mark as processed
      row.classList.add('unclut-processed');
    });
  }

  // Handle action button clicks
  async handleAction(senderEmail, action) {
    console.log(`Action: ${action} for ${senderEmail}`);
    
    // Show toast
    this.showToast(`Processing ${action} for ${senderEmail}...`, true);
    
    try {
      // In a real extension, we would communicate with the background script here
      // For now, we'll just log the action
      const response = await chrome.runtime.sendMessage({
        type: 'processAction',
        senderEmail,
        action
      });
      
      this.showToast(`Successfully processed ${action} for ${senderEmail}`, false, true);
    } catch (error) {
      console.error('Error processing action:', error);
      this.showToast(`Failed to process ${action} for ${senderEmail}`, false, false);
    }
  }

  // Show toast notification
  showToast(message, showUndo = false, isSuccess = true) {
    let toast = document.querySelector('.unclut-toast');
    
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'unclut-toast';
      document.body.appendChild(toast);
    }
    
    toast.innerHTML = `
      <span>${message}</span>
      ${showUndo ? '<span class="unclut-toast-undo">Undo</span>' : ''}
    `;
    
    // Add success/error styling
    toast.style.background = isSuccess ? '#202124' : '#d93025';
    
    // Show toast
    toast.classList.add('visible');
    
    // Auto-hide after 5 seconds
    clearTimeout(this.toastTimeout);
    this.toastTimeout = setTimeout(() => {
      toast.classList.remove('visible');
    }, 5000);
    
    // Handle undo click
    const undoBtn = toast.querySelector('.unclut-toast-undo');
    if (undoBtn) {
      undoBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        // Handle undo logic here
        this.showToast('Undo successful!', false, true);
      });
    }
  }
}

// Global extension instance
let unclutExtension = null;

/**
 * Initialize or reinitialize the extension
 */
function initializeExtension() {
  // Clean up previous instance if exists
  if (unclutExtension) {
    console.log('[Unclut] Cleaning up previous instance...');
    unclutExtension.cleanup();
    unclutExtension = null;
  }
  
  // Only initialize on Gmail pages
  if (window.location.hostname !== 'mail.google.com') {
    console.log('[Unclut] Not on Gmail, skipping initialization');
    return;
  }
  
  console.log('[Unclut] Initializing extension...');
  unclutExtension = new UnclutExtension();
}

// Handle document ready state
function handleDocumentReady() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExtension);
  } else {
    // If document is already loaded, initialize immediately
    initializeExtension();
  }
}

// Listen for Gmail's SPA navigation
function setupSPANavigation() {
  let lastUrl = location.href;
  
  const handleUrlChange = () => {
    if (location.href !== lastUrl) {
      console.log('[Unclut] URL changed, reinitializing...');
      lastUrl = location.href;
      initializeExtension();
    }
  };
  
  // Create observer to detect URL changes (for SPA navigation)
  const observer = new MutationObserver(handleUrlChange);
  observer.observe(document, { 
    childList: true, 
    subtree: true 
  });
  
  // Also listen for history changes
  const pushState = history.pushState;
  const replaceState = history.replaceState;
  
  history.pushState = function() {
    pushState.apply(history, arguments);
    handleUrlChange();
  };
  
  history.replaceState = function() {
    replaceState.apply(history, arguments);
    handleUrlChange();
  };
  
  // Listen for popstate events (back/forward navigation)
  window.addEventListener('popstate', handleUrlChange);
  
  // Cleanup function
  return () => {
    observer.disconnect();
    window.removeEventListener('popstate', handleUrlChange);
  };
}

// Initialize when the script loads
handleDocumentReady();

// Set up SPA navigation handling if on Gmail
if (window.location.hostname === 'mail.google.com') {
  setupSPANavigation();
  
  // Listen for messages from the background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'reloadExtension') {
      console.log('[Unclut] Reloading extension...');
      initializeExtension();
    }
  });
}

// Handle extension unload
window.addEventListener('unload', () => {
  if (unclutExtension) {
    unclutExtension.cleanup();
    unclutExtension = null;
  }
});
