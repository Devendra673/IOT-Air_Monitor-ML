// IoT Air Quality Monitoring - Full Application JavaScript
const API_URL = `${window.location.origin}/api`;
let currentUser = null;
let aqiChart = null;
let historyChart = null;
let refreshInterval = null;
let pendingUserId = null;  // For OTP verification
let resetToken = null;     // For password reset
let otpTimer = null;       // OTP countdown timer

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', ()=> {
    initializeApp();
});

async function initializeApp() {
    // Check authentication status
    const authStatus = await checkAuthStatus();
    
    if (authStatus.authenticated) {
        currentUser = authStatus.user;
        showMainApp();
        startAutoRefresh();
    } else {
        showLoginPage();
    }
    
    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Login form
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    
    // Register form
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('showRegisterBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterPage();
    });
    document.getElementById('showLoginBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginPage();
    });
    
    // OTP Verification
    document.getElementById('verifyOtpBtn')?.addEventListener('click', handleVerifyOTP);
    document.getElementById('resendOtpBtn')?.addEventListener('click', handleResendOTP);
    document.getElementById('otpCode')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleVerifyOTP();
    });
    
    // Password Reset
    document.getElementById('showPasswordResetBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        const modal = new bootstrap.Modal(document.getElementById('passwordResetModal'));
        modal.show();
    });
    document.getElementById('requestResetBtn')?.addEventListener('click', handleRequestPasswordReset);
    document.getElementById('resetPasswordBtn')?.addEventListener('click', handleResetPassword);
    
    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    
    // Navigation
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.getAttribute('data-page');
            navigateTo(page);
        });
    });
    
    // Export buttons
    document.getElementById('exportCsvBtn')?.addEventListener('click', exportCSV);
    document.getElementById('exportJsonBtn')?.addEventListener('click', exportJSON);
    
    // Settings form
    document.getElementById('settingsForm')?.addEventListener('submit', saveSettings);
    document.getElementById('resetSettings')?.addEventListener('click', resetSettings);
    
    // Profile page
    document.getElementById('profileForm')?.addEventListener('submit', handleUpdateProfile);
    document.getElementById('alertPreferencesForm')?.addEventListener('submit', handleUpdateAlertPreferences);
    document.getElementById('changePasswordForm')?.addEventListener('submit', handleChangePassword);
    document.getElementById('refreshSessionsBtn')?.addEventListener('click', loadUserSessions);
    
    // Add device
    document.getElementById('saveDeviceBtn')?.addEventListener('click', addDevice);
    
    // Refresh alerts
    document.getElementById('refreshAlerts')?.addEventListener('click', loadAlerts);
    
    // History time range
    document.getElementById('historyTimeRange')?.addEventListener('change', loadHistoryPage);
}

// ==================== AUTHENTICATION ====================

async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_URL}/auth/status`, {
            credentials: 'include'
        });
        return await response.json();
    } catch (error) {
        console.error('Auth check failed:', error);
        return { authenticated: false };
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const rememberMe = document.getElementById('rememberMe')?.checked || false;
    const errorDiv = document.getElementById('loginError');
    const warningDiv = document.getElementById('loginWarning');
    
    // Hide previous messages
    errorDiv?.classList.add('d-none');
    warningDiv?.classList.add('d-none');
    
    // Show loading
    AuthUI.showLoading('loginButton', 'loginLoading');
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ 
                username, 
                password,
                remember_me: rememberMe
            })
        });
        
        const data = await response.json();
        
        // Hide loading
        AuthUI.hideLoading('loginButton', 'loginLoading');
        
        if (data.success) {
            // Check for password expiry warning
            if (data.warning) {
                AuthUI.showWarning('loginWarning', data.warning);
            }
            
            // Save remember me token if provided
            if (data.remember_token) {
                RememberMeManager.setCookie('remember_token', data.remember_token, 30);
            }
            
            // Save session token
            sessionStorage.setItem('session_token', data.session_token);
            
            // Set current user
            currentUser = data.user;
            
            // Show main app
            showMainApp();
            startAutoRefresh();
            
            // Log successful login
            console.log('Login successful:', data.user.username);
        } else {
            // Handle different error cases
            if (data.requires_verification) {
                AuthUI.showError('loginError', 'Please verify your mobile number first.');
                // Optionally redirect to verification
            } else if (data.locked) {
                AuthUI.showError('loginError', data.error || 'Account is locked. Please try again later.');
            } else if (data.password_expired) {
                AuthUI.showError('loginError', data.error || 'Your password has expired. Please reset it.');
                // Show password reset modal
                document.getElementById('showPasswordResetBtn')?.click();
            } else {
                AuthUI.showError('loginError', data.error || 'Login failed');
            }
        }
    } catch (error) {
        AuthUI.hideLoading('loginButton', 'loginLoading');
        AuthUI.showError('loginError', 'Connection error. Please try again.');
        console.error('Login error:', error);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('registerFullName').value;
    const email = document.getElementById('registerEmail').value;
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    const termsAccepted = document.getElementById('acceptTerms')?.checked || false;
    const errorDiv = document.getElementById('registerError');
    const successDiv = document.getElementById('registerSuccess');
    
    // Hide previous messages
    errorDiv?.classList.add('d-none');
    successDiv?.classList.add('d-none');
    
    // Validate passwords match
    if (password !== confirmPassword) {
        AuthUI.showError('registerError', 'Passwords do not match');
        return;
    }
    
    // Validate password strength
    const passwordCheck = AuthUI.updatePasswordStrength(password);
    if (!passwordCheck.valid) {
        AuthUI.showError('registerError', 'Password does not meet security requirements');
        return;
    }
    
    // Validate username format
    const usernameValidation = FormValidator.validateUsername(username);
    if (!usernameValidation.valid) {
        AuthUI.showError('registerError', usernameValidation.message);
        return;
    }
    
    // Validate email
    if (email) {
        const emailValidation = FormValidator.validateEmail(email);
        if (!emailValidation.valid) {
            AuthUI.showError('registerError', emailValidation.message);
            return;
        }
    } else {
        AuthUI.showError('registerError', 'Email is required');
        return;
    }
    
    // Validate terms acceptance
    if (!termsAccepted) {
        AuthUI.showError('registerError', 'You must accept the Terms of Service and Privacy Policy');
        return;
    }
    
    // Show loading
    AuthUI.showLoading('registerButton', 'registerLoading');
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ 
                username: FormValidator.sanitizeInput(username, 30), 
                password,
                email: FormValidator.sanitizeInput(email, 200), 
                full_name: FormValidator.sanitizeInput(fullName, 200),
                terms_accepted: termsAccepted,
                privacy_accepted: termsAccepted
            })
        });
        
        const data = await response.json();
        
        // Hide loading
        AuthUI.hideLoading('registerButton', 'registerLoading');
        
        if (response.ok && data.success) {
            // Show success message
            AuthUI.showSuccess('registerSuccess', data.message || 'Account created successfully! Redirecting to login...');
            
            // Clear form
            document.getElementById('registerForm').reset();
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                showLoginPage();
            }, 2000);
        } else {
            // Handle validation errors
            if (data.password_errors && data.password_errors.length > 0) {
                AuthUI.showError('registerError', 'Password: ' + data.password_errors.join(', '));
            } else {
                AuthUI.showError('registerError', data.error || 'Registration failed');
            }
        }
    } catch (error) {
        AuthUI.hideLoading('registerButton', 'registerLoading');
        AuthUI.showError('registerError', 'Connection error. Please try again.');
        console.error('Registration error:', error);
    }
}

async function handleLogout(e) {
    e.preventDefault();
    
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        stopAutoRefresh();
        currentUser = null;
        showLoginPage();
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// ==================== OTP VERIFICATION ====================

async function handleVerifyOTP() {
    const otpCode = document.getElementById('otpCode').value;
    const errorDiv = document.getElementById('otpError');
    const successDiv = document.getElementById('otpSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    if (!otpCode || otpCode.length !== 6) {
        errorDiv.textContent = 'Please enter a 6-digit code';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    // Check if this is mobile setup from settings page or registration
    const isFromSettings = window.pendingMobile ? true : false;
    
    if (!pendingUserId && !isFromSettings) {
        errorDiv.textContent = 'No pending verification. Please register again.';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const requestBody = isFromSettings 
            ? { mobile_number: window.pendingMobile, otp_code: otpCode }
            : { user_id: pendingUserId, otp_code: otpCode };
            
        const response = await fetch(`${API_URL}/auth/verify-mobile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Stop timer
            if (otpTimer) clearInterval(otpTimer);
            
            if (isFromSettings) {
                // Mobile setup from settings page
                successDiv.textContent = 'Mobile verified successfully! Reloading settings...';
                successDiv.classList.remove('d-none');
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('otpModal'));
                    modal.hide();
                    document.getElementById('otpCode').value = '';
                    window.pendingMobile = null;
                    // Reload settings to show configured mobile
                    loadSettings();
                }, 2000);
            } else {
                // Registration verification
                successDiv.textContent = 'Mobile verified successfully! Redirecting to login...';
                successDiv.classList.remove('d-none');
                
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('otpModal'));
                    modal.hide();
                    document.getElementById('registerForm').reset();
                    document.getElementById('otpCode').value = '';
                    pendingUserId = null;
                    showLoginPage();
                }, 2000);
            }
        } else {
            errorDiv.textContent = data.error || 'Verification failed';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

async function handleResendOTP() {
    const errorDiv = document.getElementById('otpError');
    const successDiv = document.getElementById('otpSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    if (!pendingUserId) {
        errorDiv.textContent = 'No pending verification';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/resend-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: pendingUserId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = 'New code sent to your mobile number';
            successDiv.classList.remove('d-none');
            startOtpTimer(600); // Reset 10 minute timer
        } else {
            errorDiv.textContent = data.error || 'Failed to resend code';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

function startOtpTimer(seconds) {
    if (otpTimer) clearInterval(otpTimer);
    
    let remaining = seconds;
    const timerDisplay = document.getElementById('otpTimer');
    
    const updateTimer = () => {
        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        timerDisplay.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
        
        if (remaining <= 0) {
            clearInterval(otpTimer);
            timerDisplay.textContent = 'Expired';
        }
        remaining--;
    };
    
    updateTimer();
    otpTimer = setInterval(updateTimer, 1000);
}

// ==================== PASSWORD RESET ====================

async function handleRequestPasswordReset() {
    const identifier = document.getElementById('resetIdentifier').value;
    const errorDiv = document.getElementById('resetRequestError');
    
    errorDiv.classList.add('d-none');
    
    if (!identifier) {
        errorDiv.textContent = 'Please enter your username or mobile number';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/request-password-reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username_or_mobile: identifier })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resetToken = data.reset_token;
            
            // Show step 2
            document.getElementById('resetStep1').classList.add('d-none');
            document.getElementById('resetStep2').classList.remove('d-none');
        } else {
            errorDiv.textContent = data.error || 'Failed to send reset code';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

async function handleResetPassword() {
    const resetCode = document.getElementById('resetCode').value;
    const newPassword = document.getElementById('resetNewPassword').value;
    const confirmPassword = document.getElementById('resetConfirmPassword').value;
    const errorDiv = document.getElementById('resetError');
    const successDiv = document.getElementById('resetSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    // Validation
    if (!resetCode || resetCode.length !== 6) {
        errorDiv.textContent = 'Please enter a 6-digit reset code';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'Passwords do not match';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    if (newPassword.length < 6) {
        errorDiv.textContent = 'Password must be at least 6 characters';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                reset_token: resetToken,
                reset_code: resetCode,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = 'Password reset successful! Redirecting to login...';
            successDiv.classList.remove('d-none');
            
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('passwordResetModal'));
                modal.hide();
                
                // Reset form
                document.getElementById('resetIdentifier').value = '';
                document.getElementById('resetCode').value = '';
                document.getElementById('resetNewPassword').value = '';
                document.getElementById('resetConfirmPassword').value = '';
                document.getElementById('resetStep1').classList.remove('d-none');
                document.getElementById('resetStep2').classList.add('d-none');
                resetToken = null;
                
                showLoginPage();
            }, 2000);
        } else {
            errorDiv.textContent = data.error || 'Failed to reset password';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

// ==================== PROFILE PAGE ====================

async function loadProfile() {
    try {
        const response = await fetch(`${API_URL}/auth/profile`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success && data.user) {
            const user = data.user;
            
            // Populate profile form
            document.getElementById('profileFullName').value = user.full_name || '';
            document.getElementById('profileUsername').value = user.username || '';
            document.getElementById('profileEmail').value = user.email || '';
            document.getElementById('profileMobile').value = user.mobile_number || '';
            document.getElementById('profileRole').value = user.role || '';
            
            // Format created date
            if (user.created_at) {
                const date = new Date(user.created_at);
                document.getElementById('profileCreated').value = date.toLocaleDateString();
            }
            
            // Show mobile verified badge
            const verifiedBadge = document.getElementById('mobileVerifiedBadge');
            if (user.mobile_verified) {
                verifiedBadge.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i> Verified';
            } else {
                verifiedBadge.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i> Not Verified';
            }
            
            // Populate alert preferences
            document.getElementById('profileAlertEnabled').checked = user.alert_enabled || false;
            document.getElementById('profileNotificationPreference').value = user.notification_preference || 'sms';
        }
        
        // Load active sessions
        loadUserSessions();
    } catch (error) {
        console.error('Profile load failed:', error);
    }
}

async function handleUpdateProfile(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('profileFullName').value;
    const email = document.getElementById('profileEmail').value || null;
    const errorDiv = document.getElementById('profileUpdateError');
    const successDiv = document.getElementById('profileUpdateSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    try {
        const response = await fetch(`${API_URL}/auth/profile`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ full_name: fullName, email: email })
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = 'Profile updated successfully!';
            successDiv.classList.remove('d-none');
            
            // Update current user display
            if (currentUser) {
                currentUser.full_name = fullName;
                document.getElementById('userInfo').textContent = 
                    `${currentUser.full_name || currentUser.username} (${currentUser.role})`;
            }
        } else {
            errorDiv.textContent = data.error || 'Failed to update profile';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

async function handleUpdateAlertPreferences(e) {
    e.preventDefault();
    
    const alertEnabled = document.getElementById('profileAlertEnabled').checked;
    const notificationPreference = document.getElementById('profileNotificationPreference').value;
    const errorDiv = document.getElementById('alertPrefError');
    const successDiv = document.getElementById('alertPrefSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    try {
        // Update alert enabled
        await fetch(`${API_URL}/auth/profile`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ alert_enabled: alertEnabled })
        });
        
        // Update notification preference
        const response = await fetch(`${API_URL}/auth/update-notification-preference`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ preference: notificationPreference })
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = 'Alert preferences saved successfully!';
            successDiv.classList.remove('d-none');
        } else {
            errorDiv.textContent = data.error || 'Failed to update preferences';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

async function handleChangePassword(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;
    const errorDiv = document.getElementById('passwordError');
    const successDiv = document.getElementById('passwordSuccess');
    
    errorDiv.classList.add('d-none');
    successDiv.classList.add('d-none');
    
    // Validate passwords match
    if (newPassword !== confirmNewPassword) {
        errorDiv.textContent = 'New passwords do not match';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    if (newPassword.length < 6) {
        errorDiv.textContent = 'Password must be at least 6 characters';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ 
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            successDiv.textContent = 'Password changed successfully!';
            successDiv.classList.remove('d-none');
            
            // Clear form
            document.getElementById('changePasswordForm').reset();
        } else {
            errorDiv.textContent = data.error || 'Failed to change password';
            errorDiv.classList.remove('d-none');
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.classList.remove('d-none');
    }
}

async function loadUserSessions() {
    try {
        const response = await fetch(`${API_URL}/auth/sessions`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const sessionsList = document.getElementById('sessionsList');
        
        if (data.success && data.sessions && data.sessions.length > 0) {
            sessionsList.innerHTML = data.sessions.map(session => {
                const createdDate = new Date(session.created_at).toLocaleString();
                const lastActivity = new Date(session.last_activity).toLocaleString();
                const isCurrent = session.is_current;
                
                return `
                    <div class="list-group-item ${isCurrent ? 'border-primary' : ''}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">
                                    ${isCurrent ? '<i class="bi bi-arrow-right-circle-fill text-primary"></i> ' : ''}
                                    ${session.user_agent || 'Unknown Device'}
                                </h6>
                                <p class="mb-1 small text-muted">
                                    <i class="bi bi-geo-alt"></i> ${session.ip_address || 'Unknown IP'}<br>
                                    <i class="bi bi-clock"></i> Created: ${createdDate}<br>
                                    <i class="bi bi-activity"></i> Last: ${lastActivity}
                                </p>
                                ${isCurrent ? '<span class="badge bg-primary">Current Session</span>' : ''}
                            </div>
                            ${!isCurrent ? `
                                <button class="btn btn-sm btn-outline-danger" onclick="terminateSession(${session.id})">
                                    <i class="bi bi-x-circle"></i> End
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            sessionsList.innerHTML = '<div class="text-center text-muted">No active sessions</div>';
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
        document.getElementById('sessionsList').innerHTML = '<div class="text-center text-danger">Failed to load sessions</div>';
    }
}

async function terminateSession(sessionId) {
    if (!confirm('Are you sure you want to end this session?')) return;
    
    try {
        const response = await fetch(`${API_URL}/auth/sessions/${sessionId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Reload sessions list
            loadUserSessions();
        } else {
            alert('Failed to terminate session: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Connection error. Please try again.');
    }
}

// Make terminateSession available globally for inline onclick handlers
window.terminateSession = terminateSession;

async function showLoginPage() {
    const loginPageEl = document.getElementById('loginPage');
    const registerPageEl = document.getElementById('registerPage');
    const mainAppEl = document.getElementById('mainApp');
    
    // Load login page content
    const html = await PageLoader.load('login');
    loginPageEl.innerHTML = html;
    
    // Show/hide pages
    loginPageEl.classList.remove('d-none');
    registerPageEl.classList.add('d-none');
    mainAppEl.classList.add('d-none');
    
    // Setup password toggle
    setupPasswordToggle('loginPassword', 'toggleLoginPassword');
    
    // Re-attach event listeners
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('showRegisterBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterPage();
    });
    document.getElementById('showPasswordResetBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        const modal = new bootstrap.Modal(document.getElementById('passwordResetModal'));
        modal.show();
    });
    
    // Check for remember me token and show last login info
    const rememberToken = RememberMeManager.getCookie('remember_token');
    if (rememberToken) {
        const lastLogin = localStorage.getItem('last_login_time');
        if (lastLogin) {
            const lastLoginDate = new Date(lastLogin);
            const lastLoginInfo = document.getElementById('lastLoginInfo');
            const lastLoginText = document.getElementById('lastLoginText');
            if (lastLoginInfo && lastLoginText) {
                lastLoginText.textContent = `Last login: ${lastLoginDate.toLocaleString()}`;
                lastLoginInfo.classList.remove('d-none');
            }
        }
    }
}

async function showRegisterPage() {
    const loginPageEl = document.getElementById('loginPage');
    const registerPageEl = document.getElementById('registerPage');
    const mainAppEl = document.getElementById('mainApp');
    
    // Load register page content
    const html = await PageLoader.load('register');
    registerPageEl.innerHTML = html;
    
    // Show/hide pages
    loginPageEl.classList.add('d-none');
    registerPageEl.classList.remove('d-none');
    mainAppEl.classList.add('d-none');
    
    // Setup password toggle
    setupPasswordToggle('registerPassword', 'toggleRegisterPassword');
    
    // Setup password strength checker
    const passwordInput = document.getElementById('registerPassword');
    const confirmPasswordInput = document.getElementById('registerConfirmPassword');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            AuthUI.updatePasswordStrength(passwordInput.value);
            calculateFormProgress();
        });
    }
    
    // Setup password match checker
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', () => {
            AuthUI.checkPasswordMatch(
                document.getElementById('registerPassword').value,
                confirmPasswordInput.value
            );
            calculateFormProgress();
        });
    }
    
    // Setup form progress tracking
    const formInputs = ['registerFullName', 'registerMobile', 'registerUsername', 'registerPassword', 'registerConfirmPassword'];
    formInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', calculateFormProgress);
        }
    });
    
    const acceptTerms = document.getElementById('acceptTerms');
    if (acceptTerms) {
        acceptTerms.addEventListener('change', calculateFormProgress);
    }
    
    // Username availability check (debounced)
    const usernameInput = document.getElementById('registerUsername');
    if (usernameInput) {
        let usernameTimeout;
        usernameInput.addEventListener('input', () => {
            clearTimeout(usernameTimeout);
            usernameTimeout = setTimeout(async () => {
                const username = usernameInput.value;
                if (username.length >= 3) {
                    const validation = FormValidator.validateUsername(username);
                    const checkDiv = document.getElementById('usernameCheck');
                    if (checkDiv) {
                        checkDiv.classList.remove('d-none');
                        if (validation.valid) {
                            checkDiv.innerHTML = '<small class="text-success"><i class="bi bi-check-circle-fill"></i> Valid username format</small>';
                        } else {
                            checkDiv.innerHTML = '<small class="text-danger"><i class="bi bi-x-circle-fill"></i> ' + validation.message + '</small>';
                        }
                    }
                }
            }, 500);
        });
    }
    
    // Re-attach event listeners
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('showLoginBtn')?.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginPage();
    });
}

function showMainApp() {
    document.getElementById('loginPage').classList.add('d-none');
    document.getElementById('registerPage').classList.add('d-none');
    document.getElementById('mainApp').classList.remove('d-none');
    
    // Save last login time
    localStorage.setItem('last_login_time', new Date().toISOString());
    
    // Display user info
    document.getElementById('userInfo').textContent = 
        `${currentUser.full_name || currentUser.username} (${currentUser.role})`;
    
    // Show/hide admin nav item based on user role
    const adminNavItem = document.getElementById('adminNavItem');
    if (currentUser.role === 'admin') {
        adminNavItem.style.display = 'block';
    } else {
        adminNavItem.style.display = 'none';
    }
    
    // Show password expiry warning if needed
    if (currentUser.password_expires_in_days !== null && currentUser.password_expires_in_days <= 7) {
        showPasswordExpiryWarning(currentUser.password_expires_in_days);
    }
    
    // Load dashboard by default
    navigateTo('dashboard');
}

function showPasswordExpiryWarning(daysRemaining) {
    // Create a dismissible alert
    const alertHtml = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle-fill"></i>
            <strong>Password Expiry Warning:</strong> Your password will expire in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}. 
            <a href="#" onclick="navigateTo('profile'); return false;">Change it now</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insert at the top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertAdjacentHTML('afterbegin', alertHtml);
    }
}

// ==================== NAVIGATION ====================

function navigateTo(pageName) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Set active nav link
    document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');
    
    // Load page content into pageContainer
    const pageContainer = document.getElementById('pageContainer');
    
    // Generate page HTML based on pageName
    switch(pageName) {
        case 'dashboard':
            pageContainer.innerHTML = getDashboardHTML();
            loadDashboard();
            break;
        case 'devices':
            pageContainer.innerHTML = getDevicesHTML();
            loadDevices();
            // Reattach device listeners
            setTimeout(() => {
                document.getElementById('saveDeviceBtn')?.addEventListener('click', addDevice);
            }, 100);
            break;
        case 'history':
            pageContainer.innerHTML = getHistoryHTML();
            loadHistoryPage();
            // Reattach history listeners
            setTimeout(() => {
                document.getElementById('historyTimeRange')?.addEventListener('change', loadHistoryPage);
            }, 100);
            break;
        case 'alerts':
            pageContainer.innerHTML = getAlertsHTML();
            loadAlerts();
            // Reattach alert listeners
            setTimeout(() => {
                document.getElementById('refreshAlerts')?.addEventListener('click', loadAlerts);
            }, 100);
            break;
        case 'export':
            pageContainer.innerHTML = getExportHTML();
            // Reattach export listeners
            setTimeout(() => {
                document.getElementById('exportCsvBtn')?.addEventListener('click', exportCSV);
                document.getElementById('exportJsonBtn')?.addEventListener('click', exportJSON);
            }, 100);
            break;
        case 'settings':
            pageContainer.innerHTML = getSettingsHTML();
            loadSettings();
            // Reattach settings listeners
            setTimeout(() => {
                document.getElementById('settingsForm')?.addEventListener('submit', saveSettings);
                document.getElementById('resetSettings')?.addEventListener('click', resetSettings);
                document.getElementById('setupMobileBtn')?.addEventListener('click', setupMobileAlerts);
                document.getElementById('saveAlertPreferences')?.addEventListener('click', saveAlertPreferences);
                document.getElementById('changeMobileBtn')?.addEventListener('click', changeMobile);
                document.getElementById('saveDataRetention')?.addEventListener('click', saveDataRetention);
            }, 100);
            break;
        case 'profile':
            pageContainer.innerHTML = getProfileHTML();
            loadProfile();
            // Reattach profile listeners
            setTimeout(() => {
                document.getElementById('profileForm')?.addEventListener('submit', handleUpdateProfile);
                document.getElementById('changePasswordForm')?.addEventListener('submit', handleChangePassword);
                document.getElementById('refreshSessionsBtn')?.addEventListener('click', loadUserSessions);
            }, 100);
            break;
        case 'admin':
            // Check if user has admin role
            if (currentUser && currentUser.role === 'admin') {
                pageContainer.innerHTML = getAdminHTML();
                loadAdminPage();
            } else {
                // Non-admin users cannot access admin page
                showAlert('Access Denied: Admin privileges required', 'danger');
                navigateTo('dashboard');
            }
            break;
        default:
            pageContainer.innerHTML = getDashboardHTML();
            loadDashboard();
    }
}

// Page HTML Templates
// Note: Using modular templates when available (see page-templates.js)

function getDashboardHTML() {
    if (window.PageTemplates?.getDashboardHTML) {
        return window.PageTemplates.getDashboardHTML();
    }
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-speedometer2"></i> Dashboard</h2>
            
            <!-- Stats Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <p class="text-muted mb-1">Total Devices</p>
                                    <h3 class="mb-0" id="totalDevices">0</h3>
                                </div>
                                <div class="stat-icon bg-primary">
                                    <i class="bi bi-hdd-network"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <p class="text-muted mb-1">Total Readings</p>
                                    <h3 class="mb-0" id="totalReadings">0</h3>
                                </div>
                                <div class="stat-icon bg-info">
                                    <i class="bi bi-graph-up"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <p class="text-muted mb-1">Active Alerts</p>
                                    <h3 class="mb-0" id="activeAlerts">0</h3>
                                </div>
                                <div class="stat-icon bg-warning">
                                    <i class="bi bi-exclamation-triangle"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stat-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <p class="text-muted mb-1">System Uptime</p>
                                    <h3 class="mb-0" id="systemUptime">0h</h3>
                                </div>
                                <div class="stat-icon bg-success">
                                    <i class="bi bi-clock-history"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Latest Readings -->
            <div class="row mb-4">
                <div class="col-12">
                    <h4 class="mb-3"><i class="bi bi-speedometer"></i> Latest Readings</h4>
                    <div class="row" id="latestReadings">
                        <div class="col-12 text-center py-4">
                            <div class="spinner-border text-primary" role="status"></div>
                            <p class="mt-2">Loading devices...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Charts Row -->
            <div class="row mb-4">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="bi bi-activity"></i> 24-Hour Trend</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="aqiChart" height="300"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="bi bi-graph-up"></i> Forecast</h5>
                        </div>
                        <div class="card-body">
                            <div id="forecastTrend" class="mb-2">
                                <small class="text-muted">Trend: </small>
                                <span id="trendBadge" class="badge bg-info">Loading...</span>
                            </div>
                            <div id="forecastContainer">
                                <div class="text-center py-3">
                                    <div class="spinner-border spinner-border-sm" role="status"></div>
                                    <small class="d-block mt-2">Loading forecast...</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Alerts -->
            <div class="row">
                <div class="col-12">
                    <h4 class="mb-3"><i class="bi bi-bell"></i> Recent Alerts</h4>
                    <div id="recentAlerts">
                        <div class="text-center py-3">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="text-muted small mt-3" id="lastUpdate"></div>
        </div>
    `;
}

function getDevicesHTML() {
    if (window.PageTemplates?.getDevicesHTML) {
        return window.PageTemplates.getDevicesHTML();
    }
    return `
        <div class="container-fluid py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="bi bi-hdd-network"></i> Devices</h2>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addDeviceModal">
                    <i class="bi bi-plus-circle"></i> Add Device
                </button>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div id="devicesList">
                        <div class="text-center py-4">
                            <div class="spinner-border text-primary" role="status"></div>
                            <p class="mt-2">Loading devices...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Add Device Modal -->
            <div class="modal fade" id="addDeviceModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Register New Device</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label class="form-label">Device Name</label>
                                <input type="text" class="form-control" id="deviceName" placeholder="Living Room Sensor" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Device MAC Address</label>
                                <input type="text" class="form-control" id="deviceMac" placeholder="AA:BB:CC:DD:EE:FF" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Location</label>
                                <input type="text" class="form-control" id="deviceLocation" placeholder="Living Room, 1st Floor">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <textarea class="form-control" id="deviceDescription" rows="2"></textarea>
                            </div>
                            <div id="deviceError" class="alert alert-danger d-none"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveDeviceBtn">Save Device</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getHistoryHTML() {
    if (window.PageTemplates?.getHistoryHTML) {
        return window.PageTemplates.getHistoryHTML();
    }
    return `
        <div class="container-fluid py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="bi bi-clock-history"></i> History</h2>
                <select class="form-select" style="width: auto;" id="historyTimeRange">
                    <option value="6">Last 6 Hours</option>
                    <option value="24" selected>Last 24 Hours</option>
                    <option value="48">Last 48 Hours</option>
                    <option value="168">Last Week</option>
                </select>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-graph-up"></i> Historical Trend</h5>
                </div>
                <div class="card-body">
                    <canvas id="historyChart" height="300"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5><i class="bi bi-table"></i> Readings Table</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Temperature</th>
                                    <th>Humidity</th>
                                    <th>MQ-135</th>
                                    <th>AQI</th>
                                    <th>Category</th>
                                    <th>Anomaly</th>
                                </tr>
                            </thead>
                            <tbody id="historyTableBody">
                                <tr><td colspan="7" class="text-center py-4">
                                    <div class="spinner-border text-primary" role="status"></div>
                                    <p class="mt-2">Loading history...</p>
                                </td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getAlertsHTML() {
    if (window.PageTemplates?.getAlertsHTML) {
        return window.PageTemplates.getAlertsHTML();
    }
    return `
        <div class="container-fluid py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="bi bi-exclamation-triangle"></i> Alerts</h2>
                <button class="btn btn-outline-primary" id="refreshAlerts">
                    <i class="bi bi-arrow-clockwise"></i> Refresh
                </button>
            </div>
            
            <div class="row">
                <div class="col-lg-6">
                    <h5>Active Alerts</h5>
                    <div id="activeAlertsList">
                        <div class="text-center py-4">
                            <div class="spinner-border text-primary" role="status"></div>
                            <p class="mt-2">Loading alerts...</p>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <h5>Acknowledged Alerts</h5>
                    <div id="acknowledgedAlertsList">
                        <div class="text-center py-4">
                            <div class="spinner-border text-primary" role="status"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getExportHTML() {
    if (window.PageTemplates?.getExportHTML) {
        return window.PageTemplates.getExportHTML();
    }
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-download"></i> Export Data</h2>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="bi bi-filetype-csv"></i> Export as CSV</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Download all sensor readings in CSV format for Excel or data analysis tools.</p>
                            <button class="btn btn-primary" id="exportCsvBtn">
                                <i class="bi bi-file-earmark-spreadsheet"></i> Download CSV
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="bi bi-filetype-json"></i> Export as JSON</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Download readings in JSON format for programmatic access and custom processing.</p>
                            <button class="btn btn-primary" id="exportJsonBtn">
                                <i class="bi bi-file-earmark-code"></i> Download JSON
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getSettingsHTML() {
    if (window.PageTemplates?.getSettingsHTML) {
        return window.PageTemplates.getSettingsHTML();
    }
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-gear"></i> Settings</h2>
            
            <!-- Alert Thresholds Card -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-sliders"></i> Alert Thresholds</h5>
                </div>
                <div class="card-body">
                    <form id="settingsForm">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Warning Threshold (AQI)</label>
                                <input type="number" class="form-control" id="warningThreshold" min="0" max="500" value="100" required>
                                <small class="text-muted">Alert when AQI reaches this level</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Danger Threshold (AQI)</label>
                                <input type="number" class="form-control" id="dangerThreshold" min="0" max="500" value="150" required>
                                <small class="text-muted">Critical alert level</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Alert Frequency</label>
                            <select class="form-select" id="alertFrequency">
                                <option value="immediate">Immediate (every reading)</option>
                                <option value="hourly" selected>Every hour</option>
                                <option value="daily">Once per day</option>
                            </select>
                            <small class="text-muted">How often to send alerts when threshold is exceeded</small>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-check-circle"></i> Save Thresholds
                            </button>
                            <button type="button" class="btn btn-outline-secondary" id="resetSettings">
                                <i class="bi bi-arrow-counterclockwise"></i> Reset to Default
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Mobile Alert Setup Card -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-phone"></i> Mobile Alert Setup</h5>
                </div>
                <div class="card-body">
                    <div id="mobileNotConfigured">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i>
                            Add your mobile number to receive air quality alerts via SMS/WhatsApp.
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Mobile Number <span class="text-danger">*</span></label>
                            <input type="tel" id="setupMobile" class="form-control" placeholder="+1234567890" pattern="\+[1-9]\d{1,14}">
                            <small class="text-muted">Format: +country_code_number (e.g., +14155552671)</small>
                        </div>
                        <button class="btn btn-primary" id="setupMobileBtn">
                            <i class="bi bi-check-circle"></i> Add Mobile & Verify
                        </button>
                    </div>
                    
                    <div id="mobileConfigured" class="d-none">
                        <div class="alert alert-success">
                            <i class="bi bi-check-circle-fill"></i>
                            <strong>Mobile Verified:</strong> <span id="verifiedMobile"></span>
                        </div>
                        
                        <h6 class="mb-3">Alert Preferences</h6>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="smsEnabled" checked>
                            <label class="form-check-label" for="smsEnabled">
                                <i class="bi bi-chat-dots"></i> Enable SMS Alerts
                            </label>
                        </div>
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="whatsappEnabled">
                            <label class="form-check-label" for="whatsappEnabled">
                                <i class="bi bi-whatsapp"></i> Enable WhatsApp Alerts
                            </label>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button class="btn btn-success" id="saveAlertPreferences">
                                <i class="bi bi-check-circle"></i> Save Preferences
                            </button>
                            <button class="btn btn-outline-secondary" id="changeMobileBtn">
                                <i class="bi bi-pencil"></i> Change Mobile
                            </button>
                        </div>
                    </div>
                    
                    <div id="mobileSetupError" class="alert alert-danger d-none mt-3"></div>
                    <div id="mobileSetupSuccess" class="alert alert-success d-none mt-3"></div>
                </div>
            </div>
            
            <!-- Data Retention Card -->
            <div class="card">
                <div class="card-header">
                    <h5><i class="bi bi-database"></i> Data Retention</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Keep readings for</label>
                        <select class="form-select" id="dataRetention">
                            <option value="7">7 days</option>
                            <option value="30" selected>30 days</option>
                            <option value="90">90 days</option>
                            <option value="365">1 year</option>
                            <option value="-1">Forever</option>
                        </select>
                        <small class="text-muted">Older readings will be automatically deleted</small>
                    </div>
                    <button class="btn btn-primary" id="saveDataRetention">
                        <i class="bi bi-check-circle"></i> Save
                    </button>
                </div>
            </div>
        </div>
    `;
}

function getProfileHTML() {
    if (window.PageTemplates?.getProfileHTML) {
        return window.PageTemplates.getProfileHTML();
    }
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-person-circle"></i> Profile</h2>
            
            <!-- Profile Info -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-person"></i> Account Information</h5>
                </div>
                <div class="card-body">
                    <form id="profileForm">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Full Name</label>
                                <input type="text" class="form-control" id="profileFullName">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" class="form-control" id="profileUsername" disabled>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="profileEmail">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Mobile Number</label>
                                <input type="tel" class="form-control" id="profileMobile" placeholder="+1234567890">
                                <small class="text-muted">For SMS/WhatsApp alerts</small>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-check-circle"></i> Update Profile
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Change Password -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-key"></i> Change Password</h5>
                </div>
                <div class="card-body">
                    <form id="changePasswordForm">
                        <div class="mb-3">
                            <label class="form-label">Current Password</label>
                            <input type="password" class="form-control" id="currentPassword" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">New Password</label>
                            <input type="password" class="form-control" id="newPassword" required minlength="8">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Confirm New Password</label>
                            <input type="password" class="form-control" id="confirmNewPassword" required>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-shield-check"></i> Change Password
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Active Sessions -->
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5><i class="bi bi-laptop"></i> Active Sessions</h5>
                    <button class="btn btn-sm btn-outline-primary" id="refreshSessionsBtn">
                        <i class="bi bi-arrow-clockwise"></i> Refresh
                    </button>
                </div>
                <div class="card-body">
                    <div id="sessionsContainer">
                        <div class="text-center py-3">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            <small class="d-block mt-2">Loading sessions...</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getAdminHTML() {
    if (window.PageTemplates?.getAdminHTML) {
        return window.PageTemplates.getAdminHTML();
    }
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-shield-lock"></i> Admin Panel</h2>
            
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> <strong>Admin Access:</strong> You have full system management privileges.
            </div>
            
            <!-- System Stats -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 id="statTotalReadings">0</h2>
                            <p class="text-muted mb-0">Total Readings</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 id="statTotalDevices">0</h2>
                            <p class="text-muted mb-0">Devices</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 id="statTotalUsers">0</h2>
                            <p class="text-muted mb-0">Users</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h2 id="statDbSize">0 MB</h2>
                            <p class="text-muted mb-0">Database Size</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Admin Actions -->
            <div class="row">
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5><i class="bi bi-database"></i> Database Management</h5>
                        </div>
                        <div class="card-body">
                            <button class="btn btn-primary w-100 mb-2" onclick="createBackup()">
                                <i class="bi bi-cloud-arrow-down"></i> Create Backup
                            </button>
                            <button class="btn btn-warning w-100 mb-2" onclick="vacuumDatabase()">
                                <i class="bi bi-gear"></i> Optimize Database
                            </button>
                            <button class="btn btn-danger w-100" onclick="cleanupData()">
                                <i class="bi bi-trash"></i> Cleanup Old Data
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5><i class="bi bi-file-text"></i> System Logs</h5>
                        </div>
                        <div class="card-body">
                            <button class="btn btn-info w-100" onclick="viewLogs()">
                                <i class="bi bi-eye"></i> View System Logs
                            </button>
                            <div class="mt-3">
                                <small class="text-muted">Last reading: <span id="statLastReading">Loading...</span></small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ==================== DASHBOARD ====================

async function loadDashboard() {
    try {
        const response = await fetch(`${API_URL}/dashboard/summary`);
        const data = await response.json();
        
        // Update stats
        document.getElementById('totalDevices').textContent = data.summary.total_devices;
        document.getElementById('totalReadings').textContent = data.summary.total_readings.toLocaleString();
        document.getElementById('activeAlerts').textContent = data.summary.active_alerts;
        document.getElementById('systemUptime').textContent = `${Math.floor(data.summary.uptime_hours)}h`;
        
        // Display latest readings
        displayLatestReadings(data.latest_readings);
        
        // Display recent alerts
        displayRecentAlerts(data.recent_alerts);
        
        // Load AQI chart
        loadAQIChart();
        
        // Load forecast
        loadForecast();
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = 
            `Last update: ${new Date().toLocaleTimeString()}`;
            
    } catch (error) {
        console.error('Dashboard load failed:', error);
    }
}

function displayLatestReadings(readings) {
    const container = document.getElementById('latestReadings');
    
    if (!readings || readings.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-4">
                <i class="bi bi-exclamation-circle text-muted" style="font-size: 3rem;"></i>
                <p class="text-muted mt-2">No device data available</p>
                <p class="small">Make sure ESP32 is connected and sending data</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = readings.map(item => {
        const reading = item.reading;
        const device = item.device;
        const category = reading.category;
        const color = getAQIColor(reading.aqi);
        const textColor = getAQITextColor(reading.aqi);
        
        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card device-card h-100 border-${textColor}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div>
                                <h5 class="card-title mb-1">${device.device_name}</h5>
                                <small class="text-muted">
                                    <i class="bi bi-geo-alt"></i> ${device.location || 'Unknown'}
                                </small>
                            </div>
                            <span class="badge bg-${textColor}">
                                <span class="status-dot status-online"></span>Online
                            </span>
                        </div>
                        
                        <div class="my-3">
                            <div class="aqi-display" style="background: linear-gradient(135deg, ${color} 0%, ${getDarkerColor(color)} 100%);">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <div>
                                        <div class="aqi-label text-white">AIR QUALITY INDEX</div>
                                        <div class="aqi-number">${Math.round(reading.aqi)}</div>
                                        <div class="aqi-category-badge" style="background-color: rgba(255,255,255,0.2); color: white;">
                                            ${category}
                                        </div>
                                    </div>
                                    <div class="text-end text-white" style="opacity: 0.8;">
                                        <small>OUT OF</small>
                                        <div style="font-size: 1.5rem; font-weight: 700; line-height: 1;">500</div>
                                    </div>
                                </div>
                                <div class="aqi-scale-container">
                                    <div class="aqi-scale">
                                        <div class="aqi-indicator" style="left: ${Math.min((reading.aqi / 500) * 100, 100)}%;"></div>
                                    </div>
                                    <div class="aqi-scale-labels">
                                        <span>0</span>
                                        <span>50</span>
                                        <span>100</span>
                                        <span>150</span>
                                        <span>200</span>
                                        <span>300</span>
                                        <span>500</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row text-center mt-3">
                            <div class="col-4">
                                <i class="bi bi-thermometer text-danger"></i>
                                <div class="small">${reading.temperature.toFixed(1)}°C</div>
                            </div>
                            <div class="col-4">
                                <i class="bi bi-droplet text-info"></i>
                                <div class="small">${reading.humidity.toFixed(1)}%</div>
                            </div>
                            <div class="col-4">
                                <i class="bi bi-cloud text-secondary"></i>
                                <div class="small">${reading.mq135.toFixed(1)}</div>
                            </div>
                        </div>
                        
                        ${reading.trend ? `
                            <div class="mt-3">
                                <small class="text-muted">
                                    <i class="bi bi-graph-up"></i> Trend: <strong>${reading.trend}</strong>
                                </small>
                            </div>
                        ` : ''}
                        
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="bi bi-clock"></i> ${new Date(reading.timestamp).toLocaleTimeString()}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function displayRecentAlerts(alerts) {
    const container = document.getElementById('recentAlerts');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No recent alerts</p>';
        return;
    }
    
    container.innerHTML = alerts.map(alert => {
        const icon = alert.level === 'danger' ? 'exclamation-triangle' : 'exclamation-circle';
        const color = alert.level === 'danger' ? 'danger' : 'warning';
        
        return `
            <div class="alert alert-${color} py-2">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <i class="bi bi-${icon}"></i> <strong>${alert.alert_type}</strong>
                        <p class="mb-0 small">${alert.message}</p>
                        <small class="text-muted">${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadForecast() {
    try {
        const response = await fetch(`${API_URL}/forecast?hours=6`);
        const data = await response.json();
        
        const container = document.getElementById('forecastContainer');
        const trendBadge = document.getElementById('forecastTrend');
        
        if (!data.success) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> ${data.error}
                    <br><small>Current readings: ${data.current_readings || 0}</small>
                </div>
            `;
            trendBadge.textContent = 'Insufficient Data';
            trendBadge.className = 'badge bg-secondary';
            return;
        }
        
        // Update trend badge
        const trendColors = {
            'Improving': 'bg-success',
            'Stable': 'bg-info',
            'Worsening': 'bg-warning'
        };
        trendBadge.textContent = `${data.trend_icon} ${data.trend}`;
        trendBadge.className = `badge ${trendColors[data.trend] || 'bg-info'}`;
        
        // Display forecast cards
        container.innerHTML = `
            <div class="row">
                <div class="col-md-12 mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted">Current AQI</small>
                            <h3 class="mb-0">${data.current_aqi}</h3>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">Method</small>
                            <p class="mb-0"><small>${data.method}</small></p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                ${data.forecasts.map(f => {
                    const color = getAQIColor(f.aqi);
                    const textColor = getAQITextColor(f.aqi);
                    return `
                        <div class="col-md-4 col-6 mb-3">
                            <div class="card border-${textColor}">
                                <div class="card-body text-center">
                                    <div class="text-muted small">+${f.hour}h</div>
                                    <h4 class="text-${textColor} mb-1">${f.aqi}</h4>
                                    <div class="progress" style="height: 6px;">
                                        <div class="progress-bar bg-${textColor}" style="width: ${f.confidence}%"></div>
                                    </div>
                                    <small class="text-muted">${f.confidence}% confidence</small>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
    } catch (error) {
        console.error('Forecast load failed:', error);
        document.getElementById('forecastContainer').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Failed to load forecast
            </div>
        `;
    }
}

async function loadAQIChart() {
    try {
        const response = await fetch(`${API_URL}/readings?hours=24&limit=50`);
        const readings = await response.json();
        
        if (readings.length === 0) return;
        
        // Use actual Date objects instead of formatted strings
        const chartData = readings.reverse().map(r => ({
            x: new Date(r.timestamp),
            aqi: r.aqi,
            temp: r.temperature
        }));
        
        const aqiData = chartData.map(d => ({ x: d.x, y: d.aqi }));
        const tempData = chartData.map(d => ({ x: d.x, y: d.temp }));
        
        const ctx = document.getElementById('aqiChart').getContext('2d');
        
        if (aqiChart) {
            aqiChart.destroy();
        }
        
        aqiChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'AQI',
                    data: aqiData,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                }, {
                    label: 'Temperature (°C)',
                    data: tempData,
                    borderColor: '#e74a3b',
                    backgroundColor: 'rgba(231, 74, 59, 0.1)',
                    tension: 0.4,
                    fill: false,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'hour',
                            displayFormats: {
                                hour: 'HH:mm',
                                minute: 'HH:mm'
                            },
                            tooltipFormat: 'MMM dd, HH:mm'
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 12
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'AQI'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Chart load failed:', error);
    }
}

// ==================== DEVICES ====================

async function loadDevices() {
    const container = document.getElementById('devicesContainer');
    
    try {
        const response = await fetch(`${API_URL}/devices`);
        const devices = await response.json();
        
        if (devices.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-hdd-network text-muted" style="font-size: 4rem;"></i>
                    <h4 class="mt-3">No Devices Registered</h4>
                    <p class="text-muted">Click "Add Device" to register your first IoT device</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = devices.map(device => {
            const statusColor = device.status === 'active' ? 'success' : 'secondary';
            const statusIcon = device.status === 'active' ? 'check-circle' : 'x-circle';
            const timeSinceLastSeen = getTimeSince(device.last_seen);
            
            return `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card device-card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h5 class="card-title">${device.device_name}</h5>
                                    <p class="text-muted small mb-2">
                                        <i class="bi bi-hash"></i> ${device.device_id}
                                    </p>
                                </div>
                                <span class="badge bg-${statusColor}">
                                    <i class="bi bi-${statusIcon}"></i> ${device.status}
                                </span>
                            </div>
                            
                            <div class="mt-3">
                                <p class="mb-2">
                                    <i class="bi bi-geo-alt text-primary"></i>
                                    <strong>Location:</strong> ${device.location || 'Not set'}
                                </p>
                                <p class="mb-2">
                                    <i class="bi bi-calendar text-info"></i>
                                    <strong>Registered:</strong> ${new Date(device.registered_at).toLocaleDateString()}
                                </p>
                                <p class="mb-0">
                                    <i class="bi bi-clock text-success"></i>
                                    <strong>Last seen:</strong> ${timeSinceLastSeen}
                                </p>
                            </div>
                            
                            <div class="mt-3">
                                <button class="btn btn-sm btn-outline-primary" onclick="viewDeviceHistory('${device.id}')">
                                    <i class="bi bi-graph-up"></i> View History
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Devices load failed:', error);
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> Failed to load devices
                </div>
            </div>
        `;
    }
}

async function addDevice() {
    const deviceId = document.getElementById('newDeviceId').value;
    const deviceName = document.getElementById('newDeviceName').value;
    const location = document.getElementById('newDeviceLocation').value;
    
    try {
        const response = await fetch(`${API_URL}/devices`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ device_id: deviceId, device_name: deviceName, location })
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addDeviceModal')).hide();
            document.getElementById('addDeviceForm').reset();
            loadDevices();
        }
    } catch (error) {
        console.error('Add device failed:', error);
    }
}

function viewDeviceHistory(deviceId) {
    navigateTo('history');
    // Load history for specific device
}

// ==================== HISTORY ====================

async function loadHistoryPage() {
    const hours = parseInt(document.getElementById('historyTimeRange')?.value || 24);
    
    try {
        const response = await fetch(`${API_URL}/readings?hours=${hours}&limit=200`);
        const readings = await response.json();
        
        // Load chart
        loadHistoryChart(readings);
        
        // Load table
        loadHistoryTable(readings);
    } catch (error) {
        console.error('History load failed:', error);
    }
}

function loadHistoryChart(readings) {
    if (readings.length === 0) return;
    
    // Use actual Date objects for time-based axis
    const chartData = readings.reverse().map(r => ({
        x: new Date(r.timestamp),
        aqi: r.aqi,
        temp: r.temperature,
        hum: r.humidity
    }));
    
    const aqiData = chartData.map(d => ({ x: d.x, y: d.aqi }));
    const tempData = chartData.map(d => ({ x: d.x, y: d.temp }));
    const humData = chartData.map(d => ({ x: d.x, y: d.hum }));
    
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    if (historyChart) {
        historyChart.destroy();
    }
    
    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'AQI',
                    data: aqiData,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'Temperature (°C)',
                    data: tempData,
                    borderColor: '#e74a3b',
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Humidity (%)',
                    data: humData,
                    borderColor: '#36b9cc',
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        displayFormats: {
                            hour: 'MMM dd, HH:mm',
                            day: 'MMM dd',
                            minute: 'HH:mm'
                        },
                        tooltipFormat: 'MMM dd, yyyy HH:mm'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    ticks: {
                        maxRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: 15
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'AQI' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Temp/Humidity' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function loadHistoryTable(readings) {
    const tbody = document.getElementById('historyTableBody');
    
    if (readings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = readings.slice(0, 50).map(r => {
        const anomalyBadge = r.anomaly_detected ? 
            '<span class="badge bg-warning">Yes</span>' : 
            '<span class="badge bg-success">No</span>';
        
        return `
            <tr>
                <td>${new Date(r.timestamp).toLocaleString()}</td>
                <td>${r.temperature.toFixed(1)}°C</td>
                <td>${r.humidity.toFixed(1)}%</td>
                <td>${r.mq135.toFixed(1)}</td>
                <td><strong>${r.aqi.toFixed(1)}</strong></td>
                <td><span class="badge bg-${getAQITextColor(r.aqi)}">${r.category}</span></td>
                <td>${anomalyBadge}</td>
            </tr>
        `;
    }).join('');
}

// ==================== ALERTS ====================

async function loadAlerts() {
    const container = document.getElementById('alertsContainer');
    
    try {
        const response = await fetch(`${API_URL}/alerts?hours=168&limit=100`);
        const alerts = await response.json();
        
        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-check-circle text-success" style="font-size: 4rem;"></i>
                    <h4 class="mt-3">No Alerts</h4>
                    <p class="text-muted">System is running smoothly</p>
                </div>
            `;
            return;
        }
        
        // Group by acknowledged status
        const unacknowledged = alerts.filter(a => !a.acknowledged);
        const acknowledged = alerts.filter(a => a.acknowledged);
        
        let html = '';
        
        if (unacknowledged.length > 0) {
            html += '<h4 class="mb-3"><i class="bi bi-bell text-danger"></i> Active Alerts</h4>';
            html += unacknowledged.map(alert => createAlertCard(alert, false)).join('');
        }
        
        if (acknowledged.length > 0) {
            html += '<h4 class="mb-3 mt-4"><i class="bi bi-check2-circle text-success"></i> Acknowledged</h4>';
            html += acknowledged.map(alert => createAlertCard(alert, true)).join('');
        }
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Alerts load failed:', error);
    }
}

function createAlertCard(alert, acknowledged) {
    const color = alert.level === 'danger' ? 'danger' : 'warning';
    const icon = alert.level === 'danger' ? 'exclamation-triangle' : 'exclamation-circle';
    
    return `
        <div class="card mb-3 border-${color}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="card-title">
                            <i class="bi bi-${icon} text-${color}"></i>
                            ${alert.alert_type.replace('_', ' ').toUpperCase()}
                        </h5>
                        <p class="mb-2">${alert.message}</p>
                        ${alert.aqi_value ? `<p class="mb-0"><strong>AQI:</strong> ${alert.aqi_value.toFixed(1)}</p>` : ''}
                        <p class="text-muted small mb-0">
                            <i class="bi bi-clock"></i> ${new Date(alert.timestamp).toLocaleString()}
                        </p>
                    </div>
                    <div>
                        ${!acknowledged ? `
                            <button class="btn btn-sm btn-outline-success" onclick="acknowledgeAlert(${alert.id})">
                                <i class="bi bi-check2"></i> Acknowledge
                            </button>
                        ` : `
                            <span class="badge bg-success">Acknowledged</span>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function acknowledgeAlert(alertId) {
    try {
        const response = await fetch(`${API_URL}/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadAlerts();
        }
    } catch (error) {
        console.error('Acknowledge failed:', error);
    }
}

// ==================== SETTINGS ====================

async function loadSettings() {
    try {
        const response = await fetch(`${API_URL}/settings`);
        if (!response.ok) {
            throw new Error(`Failed to load settings (${response.status})`);
        }
        const settings = await response.json();
        
        // Populate thresholds
        const warningInput = document.getElementById('warningThreshold');
        const dangerInput = document.getElementById('dangerThreshold');
        const frequencySelect = document.getElementById('alertFrequency');
        const retentionSelect = document.getElementById('dataRetention');
        
        if (warningInput && settings.alert_threshold_unhealthy) {
            warningInput.value = settings.alert_threshold_unhealthy.value || 151;
        }
        if (dangerInput && settings.alert_threshold_dangerous) {
            dangerInput.value = settings.alert_threshold_dangerous.value || 201;
        }
        if (frequencySelect && settings.alert_cooldown_minutes) {
            const cooldown = Number(settings.alert_cooldown_minutes.value || 60);
            if (cooldown <= 0) {
                frequencySelect.value = 'immediate';
            } else if (cooldown < 1440) {
                frequencySelect.value = 'hourly';
            } else {
                frequencySelect.value = 'daily';
            }
        }
        if (retentionSelect && settings.data_retention_days) {
            retentionSelect.value = String(settings.data_retention_days.value || 30);
        }
        
        // Check if mobile alerts are enabled by admin
        const mobileAlertsValue = settings.enable_mobile_alerts ? settings.enable_mobile_alerts.value : false;
        const mobileAlertsEnabled = mobileAlertsValue === true || String(mobileAlertsValue).toLowerCase() === 'true';
        const twilioConfigured = settings.twilio_account_sid && settings.twilio_account_sid.value &&
                     settings.twilio_auth_token && settings.twilio_auth_token.value &&
                     settings.twilio_phone_number && settings.twilio_phone_number.value;
        
        const mobileAlertCard = document.querySelector('.card:has(#mobileNotConfigured)');
        const notConfiguredDiv = document.getElementById('mobileNotConfigured');

        // Preserve the original setup markup so we can restore it after admin enables Twilio.
        if (notConfiguredDiv && !notConfiguredDiv.dataset.defaultHtml) {
            notConfiguredDiv.dataset.defaultHtml = notConfiguredDiv.innerHTML;
        }

        if (!mobileAlertsEnabled || !twilioConfigured) {
            // Mobile alerts not configured by admin
            if (notConfiguredDiv) {
                notConfiguredDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        <strong>Mobile Alerts Not Available</strong>
                        <p class="mb-0 mt-2">Mobile notifications have not been configured yet. Please contact your administrator to set up Twilio integration.</p>
                    </div>
                `;
                notConfiguredDiv.classList.remove('d-none');
            }
            document.getElementById('mobileConfigured')?.classList.add('d-none');
            return;
        }

        // Twilio is configured, restore original setup markup if it was replaced by warning state.
        if (notConfiguredDiv && notConfiguredDiv.dataset.defaultHtml) {
            notConfiguredDiv.innerHTML = notConfiguredDiv.dataset.defaultHtml;
        }
        
        // Check if user has mobile configured and verified
        const userResponse = await fetch(`${API_URL}/auth/profile`, {
            credentials: 'include'
        });
        
        if (userResponse.ok) {
            const userData = await userResponse.json();
            
            if (userData.user && userData.user.mobile_number && userData.user.mobile_verified) {
                // Show configured mobile section
                document.getElementById('mobileNotConfigured')?.classList.add('d-none');
                document.getElementById('mobileConfigured')?.classList.remove('d-none');
                document.getElementById('verifiedMobile').textContent = userData.user.mobile_number;
                
                // Load alert preferences
                if (userData.user.sms_enabled !== undefined) {
                    document.getElementById('smsEnabled').checked = userData.user.sms_enabled;
                }
                if (userData.user.whatsapp_enabled !== undefined) {
                    document.getElementById('whatsappEnabled').checked = userData.user.whatsapp_enabled;
                }
            } else {
                // Show setup mobile section (Twilio is configured)
                document.getElementById('mobileNotConfigured')?.classList.remove('d-none');
                document.getElementById('mobileConfigured')?.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Settings load failed:', error);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    
    const warningThreshold = document.getElementById('warningThreshold').value;
    const dangerThreshold = document.getElementById('dangerThreshold').value;
    const alertFrequency = document.getElementById('alertFrequency').value;
    const dataRetention = document.getElementById('dataRetention')?.value;

    let cooldownMinutes = 60;
    if (alertFrequency === 'immediate') cooldownMinutes = 0;
    if (alertFrequency === 'daily') cooldownMinutes = 1440;
    
    // Validate thresholds
    if (parseInt(dangerThreshold) <= parseInt(warningThreshold)) {
        showAlert('Danger threshold must be higher than warning threshold', 'warning');
        return;
    }
    
    try {
        // Save unhealthy threshold
        const warningResponse = await fetch(`${API_URL}/settings/alert_threshold_unhealthy`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ value: warningThreshold })
        });
        if (!warningResponse.ok) {
            throw new Error(`Failed to save unhealthy threshold (${warningResponse.status})`);
        }
        
        // Save dangerous threshold
        const dangerResponse = await fetch(`${API_URL}/settings/alert_threshold_dangerous`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ value: dangerThreshold })
        });
        if (!dangerResponse.ok) {
            throw new Error(`Failed to save dangerous threshold (${dangerResponse.status})`);
        }
        
        // Save cooldown used by alert engine
        const cooldownResponse = await fetch(`${API_URL}/settings/alert_cooldown_minutes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ value: String(cooldownMinutes) })
        });
        if (!cooldownResponse.ok) {
            throw new Error(`Failed to save cooldown (${cooldownResponse.status})`);
        }

        if (dataRetention) {
            const retentionResponse = await fetch(`${API_URL}/settings/data_retention_days`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: dataRetention })
            });
            if (!retentionResponse.ok) {
                throw new Error(`Failed to save data retention (${retentionResponse.status})`);
            }
        }
        
        showAlert('Settings saved successfully!', 'success');
    } catch (error) {
        console.error('Failed to save settings:', error);
        showAlert('Failed to save settings. Please try again.', 'danger');
    }
}

function resetSettings() {
    if (confirm('Reset all settings to default values?')) {
        loadSettings();
    }
}

// ==================== MOBILE ALERT SETUP ====================

async function setupMobileAlerts() {
    const mobile = document.getElementById('setupMobile').value;
    const errorDiv = document.getElementById('mobileSetupError');
    const successDiv = document.getElementById('mobileSetupSuccess');
    
    // Hide previous messages
    errorDiv?.classList.add('d-none');
    successDiv?.classList.add('d-none');
    
    // Validate mobile number format
    if (!mobile || !mobile.match(/^\+[1-9]\d{1,14}$/)) {
        errorDiv.textContent = 'Invalid mobile number format. Use: +country_code_number (e.g., +14155552671)';
        errorDiv?.classList.remove('d-none');
        return;
    }
    
    try {
        // Send OTP to mobile
        const response = await fetch(`${API_URL}/auth/send-mobile-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ mobile_number: mobile })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Show OTP modal
            document.getElementById('otpMobileDisplay').textContent = mobile;
            const otpModal = new bootstrap.Modal(document.getElementById('otpModal'));
            otpModal.show();
            startOtpTimer(600);
            
            // Store mobile for verification
            window.pendingMobile = mobile;
            
            successDiv.textContent = 'Verification code sent! Please check your mobile.';
            successDiv?.classList.remove('d-none');
        } else {
            errorDiv.textContent = data.error || 'Failed to send verification code';
            errorDiv?.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Mobile setup failed:', error);
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv?.classList.remove('d-none');
    }
}

async function saveAlertPreferences() {
    const smsEnabled = document.getElementById('smsEnabled')?.checked || false;
    const whatsappEnabled = document.getElementById('whatsappEnabled')?.checked || false;
    
    try {
        const response = await fetch(`${API_URL}/auth/update-alert-preferences`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                sms_enabled: smsEnabled,
                whatsapp_enabled: whatsappEnabled
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showAlert('Alert preferences saved successfully!', 'success');
        } else {
            showAlert(data.error || 'Failed to save preferences', 'danger');
        }
    } catch (error) {
        console.error('Save preferences failed:', error);
        showAlert('Connection error. Please try again.', 'danger');
    }
}

function changeMobile() {
    // Show the mobile input form again
    document.getElementById('mobileNotConfigured')?.classList.remove('d-none');
    document.getElementById('mobileConfigured')?.classList.add('d-none');
    document.getElementById('setupMobile').value = '';
}

async function saveDataRetention() {
    const retention = document.getElementById('dataRetention').value;
    
    try {
        const response = await fetch(`${API_URL}/settings/data_retention_days`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ value: retention })
        });
        
        if (response.ok) {
            showAlert('Data retention settings saved!', 'success');
        } else {
            showAlert('Failed to save data retention settings', 'danger');
        }
    } catch (error) {
        console.error('Save data retention failed:', error);
        showAlert('Connection error. Please try again.', 'danger');
    }
}

// ==================== EXPORT ====================

async function exportCSV() {
    const hours = document.getElementById('csvTimeRange').value;
    window.location.href = `${API_URL}/export/csv?hours=${hours}`;
}

async function exportJSON() {
    const hours = document.getElementById('jsonTimeRange').value;
    window.location.href = `${API_URL}/export/json?hours=${hours}`;
}

// ==================== AUTO REFRESH ====================

function startAutoRefresh() {
    // Stop any existing refresh interval first
    stopAutoRefresh();
    
    // Refresh dashboard every 5 seconds
    refreshInterval = setInterval(() => {
        const currentPage = document.querySelector('.sidebar .nav-link.active')?.getAttribute('data-page');
        if (currentPage === 'dashboard') {
            loadDashboard();
        }
    }, 5000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// ==================== UTILITY FUNCTIONS ====================

function getAQIColor(aqi) {
    if (aqi <= 50) return '#00e400';
    if (aqi <= 100) return '#ffff00';
    if (aqi <= 150) return '#ff7e00';
    if (aqi <= 200) return '#ff0000';
    if (aqi <= 300) return '#8f3f97';
    return '#7e0023';
}

function getAQITextColor(aqi) {
    if (aqi <= 50) return 'success';
    if (aqi <= 100) return 'info';
    if (aqi <= 150) return 'warning';
    if (aqi <= 200) return 'warning';
    return 'danger';
}

function getDarkerColor(hexColor) {
    // Convert hex to RGB, darken by 20%, and convert back
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    
    const darken = (val) => Math.max(0, Math.floor(val * 0.7));
    
    return `#${darken(r).toString(16).padStart(2, '0')}${darken(g).toString(16).padStart(2, '0')}${darken(b).toString(16).padStart(2, '0')}`;
}

function getTimeSince(timestamp) {
    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
}

// ==================== ADMIN FUNCTIONS ====================

async function loadAdminPage() {
    // Navigation already verified admin access, just load the page data
    await loadAdminStats();
    await loadTwilioConfig();
    setupAdminListeners();
}

async function checkAdminAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/status`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (!data.authenticated) {
            showAlert('Warning: You are not logged in. Redirecting to login page...', 'warning');
            setTimeout(() => navigateTo('login'), 2000);
            return false;
        }
        
        if (data.user.role !== 'admin') {
            showAlert('Access Denied: Admin privileges required. Redirecting to dashboard...', 'danger');
            setTimeout(() => navigateTo('dashboard'), 2000);
            return false;
        }
        
        console.log('✓ Admin authentication verified:', data.user.username);
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        showAlert('Unable to verify authentication. Please refresh and login again.', 'danger');
        return false;
    }
}

function setupAdminListeners() {
    document.getElementById('createBackupBtn')?.addEventListener('click', createBackup);
    document.getElementById('listBackupsBtn')?.addEventListener('click', listBackups);
    document.getElementById('vacuumDbBtn')?.addEventListener('click', vacuumDatabase);
    document.getElementById('cleanupDataBtn')?.addEventListener('click', cleanupData);
    document.getElementById('viewLogsBtn')?.addEventListener('click', viewLogs);
    document.getElementById('twilioConfigForm')?.addEventListener('submit', saveTwilioConfig);
    document.getElementById('testTwilioBtn')?.addEventListener('click', testTwilioConnection);
}

async function loadAdminStats() {
    try {
        const response = await fetch(`${API_URL}/admin/stats`);
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            
            // Update counts
            document.getElementById('statTotalReadings').textContent = stats.counts.readings.toLocaleString();
            document.getElementById('statTotalDevices').textContent = stats.counts.devices;
            document.getElementById('statTotalUsers').textContent = stats.counts.users;
            document.getElementById('statTotalAlerts').textContent = stats.counts.alerts;
            
            // Update database info
            const dbSizeMB = (stats.database.file_size_bytes / 1024 / 1024).toFixed(2);
            document.getElementById('statDbSize').textContent = `${dbSizeMB} MB`;
            
            // Update activity
            const lastReading = stats.activity.last_reading 
                ? new Date(stats.activity.last_reading).toLocaleString()
                : 'No readings yet';
            document.getElementById('statLastReading').textContent = lastReading;
            
            // Update backup info
            document.getElementById('statBackupCount').textContent = stats.backups.total;
            
            const latestBackup = stats.backups.latest
                ? new Date(stats.backups.latest.created_at).toLocaleString()
                : 'No backups yet';
            document.getElementById('statLatestBackup').textContent = latestBackup;
        }
    } catch (error) {
        console.error('Failed to load admin stats:', error);
        showAlert('Failed to load system statistics', 'danger');
    }
}

async function createBackup() {
    const btn = document.getElementById('createBackupBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating...';
    
    try {
        const response = await fetch(`${API_URL}/admin/backup`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Backup created successfully!', 'success');
            loadAdminStats(); // Refresh stats
        } else {
            showAlert(`Failed to create backup: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Backup error:', error);
        showAlert('Failed to create backup', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function listBackups() {
    try {
        const response = await fetch(`${API_URL}/admin/backups`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('backupListContainer');
            const listDiv = document.getElementById('backupList');
            
            if (data.backups.length === 0) {
                listDiv.innerHTML = '<div class="text-muted">No backups available</div>';
            } else {
                listDiv.innerHTML = data.backups.map(backup => {
                    const sizeMB = (backup.size / 1024 / 1024).toFixed(2);
                    const date = new Date(backup.created_at).toLocaleString();
                    return `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${backup.filename}</strong><br>
                                <small class="text-muted">${date} - ${sizeMB} MB</small>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            container.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Failed to list backups:', error);
        showAlert('Failed to load backup list', 'danger');
    }
}

async function vacuumDatabase() {
    if (!confirm('This will optimize the database. Continue?')) return;
    
    const btn = document.getElementById('vacuumDbBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Optimizing...';
    
    try {
        const response = await fetch(`${API_URL}/admin/vacuum`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Database optimized successfully!', 'success');
            loadAdminStats(); // Refresh stats
        } else {
            showAlert(`Failed to optimize database: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Vacuum error:', error);
        showAlert('Failed to optimize database', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function cleanupData() {
    if (!confirm('This will remove old readings and alerts per retention policy. Continue?')) return;
    
    const btn = document.getElementById('cleanupDataBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Cleaning...';
    
    try {
        const response = await fetch(`${API_URL}/admin/cleanup`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Data cleanup completed successfully!', 'success');
            loadAdminStats(); // Refresh stats
        } else {
            showAlert(`Failed to cleanup data: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Cleanup error:', error);
        showAlert('Failed to cleanup data', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ==================== TWILIO CONFIGURATION ====================

async function loadTwilioConfig() {
    try {
        const response = await fetch(`${API_URL}/settings`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const settings = await response.json();
            
            // Populate Twilio auth token and messaging fields
            const accountSidInput = document.getElementById('twilioAccountSid');
            const authTokenInput = document.getElementById('twilioAuthToken');
            const phoneNumberInput = document.getElementById('twilioPhoneNumber');
            const whatsappNumberInput = document.getElementById('twilioWhatsappNumber');
            const adminMobileInput = document.getElementById('adminMobileNumber');
            const notificationModeInput = document.getElementById('twilioNotificationMode');
            const enableAlertsCheckbox = document.getElementById('enableMobileAlerts');
            
            if (accountSidInput && settings.twilio_account_sid) {
                accountSidInput.value = settings.twilio_account_sid.value || '';
            }
            if (authTokenInput && settings.twilio_auth_token) {
                authTokenInput.value = settings.twilio_auth_token.value || '';
            }
            if (phoneNumberInput && settings.twilio_phone_number) {
                phoneNumberInput.value = settings.twilio_phone_number.value || '';
            }
            if (whatsappNumberInput && settings.twilio_whatsapp_number) {
                whatsappNumberInput.value = settings.twilio_whatsapp_number.value || '';
            }
            if (adminMobileInput && settings.admin_mobile_number) {
                adminMobileInput.value = settings.admin_mobile_number.value || '';
            }
            if (notificationModeInput && settings.notification_type) {
                notificationModeInput.value = (settings.notification_type.value || 'sms').toLowerCase();
            }
            if (enableAlertsCheckbox && settings.enable_mobile_alerts) {
                const enableAlertsValue = settings.enable_mobile_alerts.value;
                enableAlertsCheckbox.checked = enableAlertsValue === true || String(enableAlertsValue).toLowerCase() === 'true';
            }
        }
    } catch (error) {
        console.error('Failed to load Twilio config:', error);
    }
}

async function saveTwilioConfig(e) {
    e.preventDefault();
    
    const accountSid = document.getElementById('twilioAccountSid').value.trim();
    const authToken = document.getElementById('twilioAuthToken')?.value.trim() || '';
    const phoneNumber = document.getElementById('twilioPhoneNumber').value.trim();
    const whatsappNumber = document.getElementById('twilioWhatsappNumber').value.trim();
    const adminMobile = document.getElementById('adminMobileNumber').value.trim();
    const notificationMode = (document.getElementById('twilioNotificationMode')?.value || 'sms').toLowerCase();
    const enableAlerts = document.getElementById('enableMobileAlerts').checked;
    
    // Validate required fields
    if (!accountSid || !phoneNumber) {
        showAlert('Account SID and Phone Number are required', 'danger');
        return;
    }

    if (!authToken) {
        showAlert('Auth Token is required', 'danger');
        return;
    }
    
    // Validate admin mobile number format if provided
    if (adminMobile && !adminMobile.match(/^\+[1-9]\d{1,14}$/)) {
        showAlert('Invalid admin mobile number format. Use E.164 format: +1234567890', 'danger');
        return;
    }

    if ((notificationMode === 'whatsapp' || notificationMode === 'both') && !whatsappNumber) {
        showAlert('Twilio WhatsApp number is required for WhatsApp or SMS + WhatsApp mode', 'danger');
        return;
    }
    
    try {
        // Save Twilio Auth Token settings
        const savePromises = [
            fetch(`${API_URL}/settings/twilio_account_sid`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: accountSid })
            }),
            fetch(`${API_URL}/settings/twilio_auth_token`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: authToken })
            }),
            fetch(`${API_URL}/settings/twilio_phone_number`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: phoneNumber })
            }),
            fetch(`${API_URL}/settings/twilio_whatsapp_number`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: whatsappNumber })
            }),
            fetch(`${API_URL}/settings/admin_mobile_number`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: adminMobile })
            }),
            fetch(`${API_URL}/settings/notification_type`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: notificationMode })
            }),
            fetch(`${API_URL}/settings/enable_mobile_alerts`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ value: enableAlerts.toString() })
            })
        ];
        
        const responses = await Promise.all(savePromises);
        
        // Check if any request returned 401 (not authenticated)
        const unauthorizedResponse = responses.find(r => r.status === 401);
        if (unauthorizedResponse) {
            const errorData = await unauthorizedResponse.json();
            showAlert(errorData.error || 'You must be logged in as admin to save Twilio settings.', 'danger');
            return;
        }
        
        // Check if any request returned 403 (not admin)
        const forbiddenResponse = responses.find(r => r.status === 403);
        if (forbiddenResponse) {
            const errorData = await forbiddenResponse.json();
            showAlert(errorData.error || 'Admin access required. You must be logged in as an administrator.', 'danger');
            return;
        }
        
        // Check if all requests were successful
        const allSuccessful = responses.every(r => r.ok);
        if (!allSuccessful) {
            showAlert('Some settings failed to save. Please check your login status and try again.', 'danger');
            return;
        }
        
        showAlert('Twilio configuration saved successfully using Auth Token! Settings are active immediately.', 'success');
    } catch (error) {
        console.error('Failed to save Twilio config:', error);
        showAlert('Failed to save configuration. Make sure you are logged in as admin and try again.', 'danger');
    }
}

async function testTwilioConnection() {
    const btn = document.getElementById('testTwilioBtn');
    const resultDiv = document.getElementById('twilioTestResult');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing...';
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch(`${API_URL}/admin/test-twilio`, {
            method: 'POST',
            credentials: 'include'
        });
        
        // Check for authentication error
        if (response.status === 401) {
            showAlert('You must be logged in as admin to test Twilio connection', 'danger');
            resultDiv.innerHTML = `
                <div class="alert alert-danger mt-3">
                    <i class="bi bi-exclamation-triangle-fill"></i> <strong>Authentication Required</strong><br>
                    You must be logged in as an administrator to test the Twilio connection.
                    <hr>
                    <strong>Please:</strong>
                    <ol class="mb-0 small">
                        <li>Click "Logout" (if currently logged in as regular user)</li>
                        <li>Click "Login" in the top navigation</li>
                        <li>Use admin credentials: <code>admin</code> / <code>admin123</code></li>
                        <li>Return to Admin Panel and try again</li>
                    </ol>
                </div>
            `;
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`✓ Test successful! ${data.message}`, 'success');
            resultDiv.innerHTML = `
                <div class="alert alert-success mt-3">
                    <i class="bi bi-check-circle-fill"></i> <strong>Connection Successful!</strong><br>
                    ${data.message}<br>
                    <small class="text-muted">Check your mobile phone for the test SMS.</small>
                </div>
            `;
        } else {
            showAlert(`✗ Test failed: ${data.error}`, 'danger');
            resultDiv.innerHTML = `
                <div class="alert alert-danger mt-3">
                    <i class="bi bi-x-circle-fill"></i> <strong>Connection Failed</strong><br>
                    ${data.error}
                    
                    <hr>
                    <small><strong>Common Solutions:</strong></small>
                    <ul class="mb-0 small">
                        <li>Verify Account SID and Auth Token are correct (no extra spaces)</li>
                        <li>Check phone number format: +1234567890 (E.164 format)</li>
                        <li><strong>Trial Accounts:</strong> Admin mobile must be verified in 
                            <a href="https://console.twilio.com/us1/develop/phone-numbers/manage/verified" target="_blank" class="alert-link">
                                Twilio Console <i class="bi bi-box-arrow-up-right"></i>
                            </a>
                        </li>
                        <li>Save configuration before testing</li>
                    </ul>
                </div>
            `;
        }
    } catch (error) {
        console.error('Twilio test failed:', error);
        showAlert('Network error. Please try again.', 'danger');
        resultDiv.innerHTML = `
            <div class="alert alert-danger mt-3">
                <i class="bi bi-exclamation-triangle-fill"></i> <strong>Network Error</strong><br>
                ${error.message}<br>
                <small>Make sure the server is running and you are logged in as admin.</small>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function viewLogs() {
    showAlert('Log viewing feature coming soon! Logs are stored in the /logs directory on the server.', 'info');
}

function showAlert(message, type) {
    // Use modular utility if available, fallback to inline implementation
    if (window.ModularUtils && window.ModularUtils.showAlert) {
        return window.ModularUtils.showAlert(message, type);
    }
    
    // Fallback implementation (for backward compatibility)
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}
