/**
 * Module Bridge - Makes ES6 modules available globally
 * This allows gradual migration without breaking existing code
 */

// Import ES6 modules
import { API_URL, state } from './config.js';
import * as Utils from './utils.js';
import * as Templates from './page-templates.js';

// Expose as global objects for compatibility with existing code
window.ModularUtils = Utils;
window.PageTemplates = Templates;

// Also expose individual frequently-used functions globally
window.showAlert = Utils.showAlert;
window.getAqiCategory = Utils.getAqiCategory;
window.formatDate = Utils.formatDate;

// Make config available
window.ModularConfig = { API_URL, state };

console.log('✅ Modular utilities loaded and available globally');
console.log('📦 Available: ModularUtils, PageTemplates, showAlert, getAqiCategory, formatDate');
