// Background script for unclut.ai Gmail extension

// Initialize extension state
const state = {
  isAuthenticated: false,
  currentUser: null,
  lastAction: null
};

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('unclut.ai extension installed');
  // Set up initial storage
  chrome.storage.sync.set({ settings: {} });
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'processAction') {
    handleAction(request.senderEmail, request.action)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Will respond asynchronously
  }
  
  // Add more message handlers as needed
});

// Handle action processing
async function handleAction(senderEmail, action) {
  console.log(`Processing ${action} for ${senderEmail}`);
  
  try {
    // Ensure we're authenticated
    await ensureAuthenticated();
    
    // Process the requested action
    switch (action) {
      case 'unsubscribe':
        return await processUnsubscribe(senderEmail);
      case 'delete':
        return await processDelete(senderEmail);
      case 'both':
        const [unsubResult, deleteResult] = await Promise.all([
          processUnsubscribe(senderEmail),
          processDelete(senderEmail)
        ]);
        return { unsubResult, deleteResult };
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  } catch (error) {
    console.error('Error processing action:', error);
    throw error;
  }
}

// Process unsubscribe action
async function processUnsubscribe(senderEmail) {
  console.log(`Attempting to unsubscribe from ${senderEmail}`);
  
  try {
    // In a real implementation, we would:
    // 1. Find the unsubscribe link in the most recent email
    // 2. Follow the unsubscribe flow
    // 3. Return the result
    
    // For now, we'll simulate a successful unsubscribe
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      message: `Successfully unsubscribed from ${senderEmail}`,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error unsubscribing:', error);
    throw new Error(`Failed to unsubscribe from ${senderEmail}`);
  }
}

// Process delete action
async function processDelete(senderEmail) {
  console.log(`Attempting to delete emails from ${senderEmail}`);
  
  try {
    // In a real implementation, we would:
    // 1. Query Gmail API for messages from this sender
    // 2. Batch delete the messages
    // 3. Return the result
    
    // For now, we'll simulate a successful deletion
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      message: `Successfully deleted emails from ${senderEmail}`,
      timestamp: new Date().toISOString(),
      count: 42 // Simulated count of deleted emails
    };
  } catch (error) {
    console.error('Error deleting emails:', error);
    throw new Error(`Failed to delete emails from ${senderEmail}`);
  }
}

// Ensure user is authenticated
async function ensureAuthenticated() {
  if (state.isAuthenticated) return true;
  
  try {
    // Request Gmail API access
    const token = await new Promise((resolve, reject) => {
      chrome.identity.getAuthToken({ interactive: true }, (token) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError));
        } else {
          resolve(token);
        }
      });
    });
    
    // Get user info
    const userInfo = await fetchUserInfo(token);
    
    // Update state
    state.isAuthenticated = true;
    state.currentUser = userInfo;
    
    return true;
  } catch (error) {
    console.error('Authentication failed:', error);
    throw new Error('Authentication required. Please sign in to continue.');
  }
}

// Fetch user info using the access token
async function fetchUserInfo(token) {
  const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch user info');
  }
  
  return await response.json();
}

// Handle OAuth redirect
chrome.identity.onSignInChanged.addListener((accountId) => {
  console.log('Sign in state changed:', accountId);
  state.isAuthenticated = !!accountId;
  state.currentUser = accountId ? { email: accountId } : null;
});
