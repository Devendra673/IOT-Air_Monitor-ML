/**
 * Professional Authentication Utilities
 * Password strength checking, form validation, UI enhancements
 */

// Password Strength Checker
class PasswordStrengthChecker {
    constructor() {
        this.commonPasswords = new Set([
            'password', 'password123', '12345678', 'qwerty', 'abc123',
            'monkey', '1234567890', 'letmein', 'trustno1', 'dragon',
            'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
            'bailey', 'shadow', '123123', '654321', 'superman',
            'admin', 'admin123', 'root', 'toor', 'pass', 'test'
        ]);
    }
    
    check(password) {
        let score = 0;
        let feedback = {
            errors: [],
            suggestions: [],
            passed: []
        };
        
        // Length check
        if (password.length < 8) {
            feedback.errors.push('Password must be at least 8 characters');
        } else {
            score += Math.min(25, password.length * 2);
            feedback.passed.push('length');
        }
        
        // Uppercase check
        if (!/[A-Z]/.test(password)) {
            feedback.errors.push('Add uppercase letters');
        } else {
            score += 15;
            feedback.passed.push('uppercase');
        }
        
        // Lowercase check
        if (!/[a-z]/.test(password)) {
            feedback.errors.push('Add lowercase letters');
        } else {
            score += 15;
            feedback.passed.push('lowercase');
        }
        
        // Number check
        if (!/\d/.test(password)) {
            feedback.errors.push('Add numbers');
        } else {
            score += 15;
            feedback.passed.push('number');
        }
        
        // Special character check
        if (!/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;'`~]/.test(password)) {
            feedback.errors.push('Add special characters');
        } else {
            score += 15;
            feedback.passed.push('special');
        }
        
        // Common password check
        if (this.commonPasswords.has(password.toLowerCase())) {
            feedback.errors.push('Password is too common');
            score = Math.max(0, score - 30);
        }
        
        // Sequential characters check
        if (this.hasSequential(password)) {
            feedback.suggestions.push('Avoid sequential characters (abc, 123)');
            score -= 10;
        }
        
        // Repeated characters check
        if (this.hasRepeated(password)) {
            feedback.suggestions.push('Avoid repeated characters (aaa, 111)');
            score -= 10;
        }
        
        // Calculate strength
        score = Math.max(0, Math.min(100, score));
        let strength = 'weak';
        let color = 'danger';
        
        if (score < 30) {
            strength = 'weak';
            color = 'danger';
        } else if (score < 50) {
            strength = 'fair';
            color = 'warning';
        } else if (score < 70) {
            strength = 'good';
            color = 'info';
        } else if (score < 90) {
            strength = 'strong';
            color = 'success';
        } else {
            strength = 'very_strong';
            color = 'success';
        }
        
        return {
            score,
            strength,
            color,
            valid: feedback.errors.length === 0,
            feedback
        };
    }
    
    hasSequential(password) {
        const sequential = [
            'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
            'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
            'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz',
            '123', '234', '345', '456', '567', '678', '789', '890'
        ];
        const lower = password.toLowerCase();
        return sequential.some(seq => lower.includes(seq));
    }
    
    hasRepeated(password) {
        for (let i = 0; i < password.length - 2; i++) {
            if (password[i] === password[i + 1] && password[i] === password[i + 2]) {
                return true;
            }
        }
        return false;
    }
}

// Form Validation Utilities
class FormValidator {
    static validateUsername(username) {
        const pattern = /^[a-zA-Z0-9_-]{3,30}$/;
        return {
            valid: pattern.test(username),
            message: pattern.test(username) 
                ? 'Username is available' 
                : 'Username must be 3-30 characters, alphanumeric, underscore or dash only'
        };
    }
    
    static validateEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return {
            valid: pattern.test(email),
            message: pattern.test(email) ? 'Valid email' : 'Invalid email format'
        };
    }
    
    static validateMobile(mobile) {
        const pattern = /^\+[1-9]\d{1,14}$/;
        return {
            valid: pattern.test(mobile),
            message: pattern.test(mobile) 
                ? 'Valid mobile number' 
                : 'Mobile must be in E.164 format (+country_code_number)'
        };
    }
    
    static sanitizeInput(text, maxLength = 255) {
        // Remove potentially dangerous characters
        text = text.replace(/[<>"'%;()&+]/g, '');
        return text.substring(0, maxLength).trim();
    }
}

// UI Enhancement Utilities
class AuthUI {
    static showLoading(buttonId, loadingId) {
        document.getElementById(buttonId)?.classList.add('d-none');
        document.getElementById(loadingId)?.classList.remove('d-none');
    }
    
    static hideLoading(buttonId, loadingId) {
        document.getElementById(buttonId)?.classList.remove('d-none');
        document.getElementById(loadingId)?.classList.add('d-none');
    }
    
    static showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('d-none');
            setTimeout(() => element.classList.add('d-none'), 5000);
        }
    }
    
    static showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('d-none');
            setTimeout(() => element.classList.add('d-none'), 5000);
        }
    }
    
    static showWarning(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.classList.remove('d-none');
        }
    }
    
    static updateProgress(progressBarId, progressPercentId, percent) {
        const bar = document.getElementById(progressBarId);
        const text = document.getElementById(progressPercentId);
        
        if (bar) {
            bar.style.width = `${percent}%`;
            bar.setAttribute('aria-valuenow', percent);
        }
        
        if (text) {
            text.textContent = Math.round(percent);
        }
    }
    
    static updatePasswordStrength(password) {
        const checker = new PasswordStrengthChecker();
        const result = checker.check(password);
        
        const bar = document.getElementById('passwordStrengthBar');
        const text = document.getElementById('passwordStrengthText');
        const requirements = document.getElementById('passwordRequirements');
        
        if (bar) {
            bar.style.width = `${result.score}%`;
            bar.className = `progress-bar password-${result.strength.replace('_', '-')}`;
        }
        
        if (text) {
            text.textContent = result.strength.replace('_', ' ').toUpperCase();
            text.className = `fw-bold text-${result.color}`;
        }
        
        // Update requirements checklist
        if (requirements && password.length > 0) {
            requirements.classList.remove('d-none');
            
            // Length
            this.updateRequirement('req-length', password.length >= 8);
            // Uppercase
            this.updateRequirement('req-uppercase', /[A-Z]/.test(password));
            // Lowercase
            this.updateRequirement('req-lowercase', /[a-z]/.test(password));
            // Number
            this.updateRequirement('req-number', /\d/.test(password));
            // Special
            this.updateRequirement('req-special', /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;'`~]/.test(password));
        } else if (requirements) {
            requirements.classList.add('d-none');
        }
        
        return result;
    }
    
    static updateRequirement(elementId, passed) {
        const element = document.getElementById(elementId);
        if (element) {
            if (passed) {
                element.className = 'text-success';
                element.querySelector('i').className = 'bi bi-check-circle-fill';
            } else {
                element.className = 'text-danger';
                element.querySelector('i').className = 'bi bi-circle';
            }
        }
    }
    
    static checkPasswordMatch(password, confirmPassword) {
        const matchElement = document.getElementById('passwordMatch');
        
        if (!matchElement || confirmPassword.length === 0) {
            if (matchElement) matchElement.classList.add('d-none');
            return false;
        }
        
        matchElement.classList.remove('d-none');
        
        if (password === confirmPassword) {
            matchElement.innerHTML = '<small class="text-success"><i class="bi bi-check-circle-fill"></i> Passwords match</small>';
            return true;
        } else {
            matchElement.innerHTML = '<small class="text-danger"><i class="bi bi-x-circle-fill"></i> Passwords do not match</small>';
            return false;
        }
    }
}

// Password Toggle Utility
function setupPasswordToggle(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    
    if (button && input) {
        button.addEventListener('click', () => {
            const type = input.type === 'password' ? 'text' : 'password';
            input.type = type;
            
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = type === 'password' ? 'bi bi-eye' : 'bi bi-eye-slash';
            }
        });
    }
}

// Form Progress Tracking
function calculateFormProgress() {
    const fullName = document.getElementById('registerFullName')?.value || '';
    const email = document.getElementById('registerEmail')?.value || '';
    const username = document.getElementById('registerUsername')?.value || '';
    const password = document.getElementById('registerPassword')?.value || '';
    const confirmPassword = document.getElementById('registerConfirmPassword')?.value || '';
    const terms = document.getElementById('acceptTerms')?.checked || false;
    
    let progress = 0;
    
    if (fullName.length > 0) progress += 16.67;
    if (email.length > 0) progress += 16.67;
    if (username.length > 0) progress += 16.67;
    if (password.length >= 8) progress += 16.67;
    if (confirmPassword === password && password.length > 0) progress += 16.67;
    if (terms) progress += 20;  // Last field worth more
    
    AuthUI.updateProgress('progressBar', 'progressPercent', progress);
}

// Remember Me Cookie Management
class RememberMeManager {
    static setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Strict;Secure`;
    }
    
    static getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
    
    static deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
}

// Export utilities
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PasswordStrengthChecker,
        FormValidator,
        AuthUI,
        setupPasswordToggle,
        calculateFormProgress,
        RememberMeManager
    };
}
