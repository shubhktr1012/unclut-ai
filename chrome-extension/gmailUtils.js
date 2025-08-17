/**
 * Gmail-specific DOM utilities
 */

/**
 * Get the email address from a Gmail message row
 * @param {HTMLElement} row - The message row element
 * @returns {string|null} - The email address or null if not found
 */
function getSenderEmail(row) {
  // Try different selectors used by Gmail
  const emailElement = row.querySelector('[email]');
  if (emailElement) {
    return emailElement.getAttribute('email');
  }
  
  // Fallback for different Gmail layouts
  const nameElement = row.querySelector('[name]');
  if (nameElement) {
    return nameElement.getAttribute('name');
  }
  
  return null;
}

/**
 * Get the display name of the sender from a Gmail message row
 * @param {HTMLElement} row - The message row element
 * @returns {string} - The display name or email if name not found
 */
function getSenderDisplayName(row) {
  const nameElement = row.querySelector('[name]');
  if (nameElement && nameElement.textContent) {
    return nameElement.textContent.trim();
  }
  
  // Fallback to email if name not found
  return getSenderEmail(row) || 'Unknown Sender';
}

/**
 * Check if an email is from a mailing list
 * @param {HTMLElement} row - The message row element
 * @returns {boolean} - True if the email is from a mailing list
 */
function isMailingList(row) {
  // Check for common mailing list indicators
  const subject = row.querySelector('[data-thread-id]')?.textContent || '';
  const from = row.textContent || '';
  
  return (
    subject.includes('unsubscribe') ||
    from.includes('mailing list') ||
    from.includes('newsletter') ||
    from.includes('noreply@')
  );
}

/**
 * Find the best position to insert our action button
 * @param {HTMLElement} row - The message row element
 * @returns {HTMLElement|null} - The element to insert before or null if not found
 */
function getInsertionPoint(row) {
  // Try to find the star/important icon
  const starButton = row.querySelector('[role="button"][title*="Star"]');
  if (starButton) {
    return starButton.nextElementSibling;
  }
  
  // Fallback to the first button in the row
  const firstButton = row.querySelector('[role="button"]');
  if (firstButton) {
    return firstButton.nextElementSibling;
  }
  
  return null;
}

export {
  getSenderEmail,
  getSenderDisplayName,
  isMailingList,
  getInsertionPoint
};
