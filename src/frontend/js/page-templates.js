/**
 * HTML Template Functions for All Pages
 */

export function getDashboardHTML() {
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

export function getDevicesHTML() {
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

export function getHistoryHTML() {
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

export function getAlertsHTML() {
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

export function getExportHTML() {
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

export function getSettingsHTML() {
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
                        
                        <div id="mobileSetupError" class="alert alert-danger d-none"></div>
                        <div id="mobileSetupSuccess" class="alert alert-success d-none"></div>
                        
                        <div class="mb-3">
                            <label class="form-label">Mobile Number <span class="text-danger">*</span></label>
                            <input type="tel" id="setupMobile" class="form-control" placeholder="+1234567890" pattern="\\+[1-9]\\d{1,14}">
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

export function getProfileHTML() {
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
                                <input type="tel" class="form-control" id="profileMobile" disabled>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Update Profile</button>
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
                            <input type="password" class="form-control" id="newPassword" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Confirm New Password</label>
                            <input type="password" class="form-control" id="confirmNewPassword" required>
                        </div>
                        <button type="submit" class="btn btn-primary">Change Password</button>
                    </form>
                </div>
            </div>
            
            <!-- Active Sessions -->
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5><i class="bi bi-pc-display"></i> Active Sessions</h5>
                    <button class="btn btn-sm btn-outline-primary" id="refreshSessionsBtn">
                        <i class="bi bi-arrow-clockwise"></i> Refresh
                    </button>
                </div>
                <div class="card-body">
                    <div id="sessionsList">
                        <div class="text-center py-3">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            <p class="mt-2">Loading sessions...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

export function getAdminHTML() {
    return `
        <div class="container-fluid py-4">
            <h2 class="mb-4"><i class="bi bi-shield-lock"></i> System Administration</h2>
            
            <!-- System Stats -->
            <h4 class="mb-3">System Statistics</h4>
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <p class="text-muted">Total Readings</p>
                            <h3 id="statTotalReadings">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <p class="text-muted">Total Devices</p>
                            <h3 id="statTotalDevices">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <p class="text-muted">Total Users</p>
                            <h3 id="statTotalUsers">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <p class="text-muted">Database Size</p>
                            <h3 id="statDbSize">0 MB</h3>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Notification Configuration -->
            <h4 class="mb-3">Mobile Notification Setup</h4>
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="bi bi-bell"></i> Twilio Configuration (Auth Token)</h5>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i> Configure Twilio using <strong>Auth Token authentication</strong> for SMS/WhatsApp alerts.
                        <a href="https://www.twilio.com/console" target="_blank">Get credentials from Twilio Console</a>
                    </div>
                    
                    <form id="twilioConfigForm">
                        <!-- Account SID -->
                        <div class="mb-3">
                            <label class="form-label">Twilio Account SID <span class="text-danger">*</span></label>
                            <input type="text" class="form-control" id="twilioAccountSid" placeholder="ACxxxxxx..." required>
                            <small class="text-muted">Found in Twilio Console dashboard (starts with "AC", 34 characters)</small>
                        </div>

                        <!-- Auth Token Field -->
                        <div class="mb-3" id="authTokenField">
                            <label class="form-label">Auth Token <span class="text-danger">*</span></label>
                            <input type="password" class="form-control" id="twilioAuthToken" placeholder="Enter Twilio Auth Token">
                            <small class="text-muted">Found in Twilio Console under Account Info</small>
                        </div>
                        
                        <hr>
                        
                        <!-- Phone Numbers -->
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Twilio Phone Number <span class="text-danger">*</span></label>
                                <input type="tel" class="form-control" id="twilioPhoneNumber" placeholder="+1234567890" required>
                                <small class="text-muted">Your Twilio phone number (E.164 format)</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Twilio WhatsApp Number (Optional)</label>
                                <input type="tel" class="form-control" id="twilioWhatsappNumber" placeholder="whatsapp:+14155238886">
                                <small class="text-muted">Twilio WhatsApp sandbox number</small>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Admin Mobile Number <span class="text-danger">*</span></label>
                                <input type="tel" class="form-control" id="adminMobileNumber" placeholder="+1234567890" required>
                                <small class="text-muted">Your mobile number for test messages (must be verified in Twilio for trial accounts)</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Alert Mode <span class="text-danger">*</span></label>
                                <select class="form-select" id="twilioNotificationMode">
                                    <option value="sms">SMS Only</option>
                                    <option value="whatsapp">WhatsApp Only</option>
                                    <option value="both">SMS + WhatsApp</option>
                                </select>
                                <small class="text-muted">Choose how admin alerts are delivered.</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="enableMobileAlerts">
                                <label class="form-check-label" for="enableMobileAlerts">
                                    Enable Mobile Notifications System
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2 mb-3">
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-check-circle"></i> Save Configuration
                            </button>
                            <button type="button" class="btn btn-outline-secondary" id="testTwilioBtn">
                                <i class="bi bi-check2-circle"></i> Test Connection
                            </button>
                        </div>
                        
                        <!-- Test Result Message -->
                        <div id="twilioTestResult"></div>
                    </form>
                </div>
            </div>

            <!-- Database Management -->
            <h4 class="mb-3">Database Management</h4>
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <button class="btn btn-primary w-100" id="createBackupBtn">
                                <i class="bi bi-shield-check"></i> Create Backup
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-info w-100" id="vacuumDbBtn">
                                <i class="bi bi-arrow-repeat"></i> Optimize DB
                            </button>
                        </div>
                        <div class="col-md-4">
                            <button class="btn btn-warning w-100" id="cleanupDataBtn">
                                <i class="bi bi-trash"></i> Cleanup Old Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}
