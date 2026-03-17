/**
 * Utility Functions for IoT Air Quality Monitoring System
 */

/**
 * Display alert message to user
 * @param {string} message - The message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 */
export function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

/**
 * Get AQI category and color based on value
 * @param {number} aqi - Air Quality Index value
 * @returns {Object} - {category, color, description}
 */
export function getAqiCategory(aqi) {
    if (aqi <= 50) {
        return { category: 'Good', color: 'success', description: 'Air quality is satisfactory' };
    } else if (aqi <= 100) {
        return { category: 'Moderate', color: 'warning', description: 'Air quality is acceptable' };
    } else if (aqi <= 150) {
        return { category: 'Unhealthy for Sensitive Groups', color: 'orange', description: 'Sensitive groups may experience health effects' };
    } else if (aqi <= 200) {
        return { category: 'Unhealthy', color: 'danger', description: 'Everyone may begin to experience health effects' };
    } else if (aqi <= 300) {
        return { category: 'Very Unhealthy', color: 'danger', description: 'Health alert: everyone may experience serious effects' };
    } else {
        return { category: 'Hazardous', color: 'danger', description: 'Health warning of emergency conditions' };
    }
}

/**
 * Format date to readable string
 * @param {string|Date} dateString - Date to format
 * @returns {string} - Formatted date string
 */
export function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string|Date} dateString - Date to format
 * @returns {string} - Relative time string
 */
export function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return `${seconds} second${seconds !== 1 ? 's' : ''} ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days !== 1 ? 's' : ''} ago`;
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid
 */
export function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate mobile number format (+country_code + number)
 * @param {string} mobile - Mobile number to validate
 * @returns {boolean} - True if valid
 */
export function isValidMobile(mobile) {
    const re = /^\+[1-9]\d{1,14}$/;
    return re.test(mobile);
}

/**
 * Check password strength
 * @param {string} password - Password to check
 * @returns {Object} - {strength, score, feedback}
 */
export function checkPasswordStrength(password) {
    let score = 0;
    const feedback = [];
    
    if (password.length >= 8) score += 1;
    else feedback.push('At least 8 characters');
    
    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('Lowercase letter');
    
    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('Uppercase letter');
    
    if (/[0-9]/.test(password)) score += 1;
    else feedback.push('Number');
    
    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    else feedback.push('Special character');
    
    const strengths = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
    const strength = strengths[score];
    
    return { strength, score, feedback, isValid: score >= 4 };
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Safely parse JSON with fallback
 * @param {string} jsonString - JSON string to parse
 * @param {*} fallback - Fallback value if parsing fails
 * @returns {*} - Parsed object or fallback
 */
export function safeJsonParse(jsonString, fallback = null) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('JSON parse error:', error);
        return fallback;
    }
}

/**
 * Download data as file
 * @param {string} data - Data to download
 * @param {string} filename - Filename
 * @param {string} mimeType - MIME type
 */
export function downloadFile(data, filename, mimeType = 'text/plain') {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} - True if successful
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('Failed to copy:', error);
        return false;
    }
}
