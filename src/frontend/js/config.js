/**
 * Configuration and Constants
 */

// API Configuration
export const API_URL = 'http://localhost:5000/api';

// Global State
export const state = {
    currentUser: null,
    pendingUserId: null,
    pendingMobile: null,
    otpTimer: null,
    refreshInterval: null,
    aqiChart: null,
    historyChart: null
};

// Export for window access (for compatibility with existing code)
window.API_URL = API_URL;
