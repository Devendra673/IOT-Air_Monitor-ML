# IoT Air Quality Monitoring System with ML Prediction

Professional-grade air quality monitoring system using IoT sensors, machine learning predictions, and real-time alerts.

---

## 🌟 Major Features

### 1. **Professional User Authentication**
- **Simple Registration**: Create account with name, username, email, and password
- **Password Security**: Real-time strength checker with 5 security requirements
- **Remember Me**: Persistent 30-day sessions
- **Account Protection**: Auto-lockout after 5 failed login attempts
- **Session Management**: View and revoke active sessions
- **Login History**: Track all login attempts with IP, device, and location

### 2. **Real-Time Air Quality Monitoring**
- **Live Sensor Data**: Real-time readings from MQ-135 air quality sensor, DHT11 (temperature/humidity)
- **AQI Calculation**: Automatic Air Quality Index with health recommendations
- **Visual Dashboard**: Real-time charts, gauges, and trend analysis
- **24-Hour History**: Scrolling time-series visualization

### 3. **Machine Learning Predictions**
- **Random Forest Model**: Trained on 15,000+ data points
- **24-Hour Forecast**: Predict air quality trends
- **95%+ Accuracy**: Validated model with comprehensive testing
- **Smart Alerts**: Predictive warnings before air quality degrades

### 4. **Alert System** (Mobile Setup Optional)
- **Configurable Thresholds**: Set custom AQI warning levels
- **Multiple Channels**: SMS and WhatsApp notifications (when mobile added)
- **Smart Notifications**: Avoid alert fatigue with intelligent filtering
- **Alert History**: Review all past alerts

### 5. **Data Management**
- **Automatic Backups**: Daily database backups with 30-day retention
- **Data Export**: Download readings as CSV
- **Bulk Upload**: Import historical data
- **Data Cleanup**: Automatic removal of old readings

---

## 🚀 Quick Setup (5 Minutes)

### Prerequisites
- Python 3.8 or higher
- Arduino (optional - for hardware sensors)

### Step 1: Install Dependencies
```powershell
# Navigate to project directory
cd IoT_ML_Project

# (Recommended) Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Start the Server
```powershell
python run.py
```

The server will start at **http://localhost:5000**

### Step 3: Create Your Account
1. Open browser to **http://localhost:5000**
2. Click **"Create New Account"**
3. Fill in the form:
   - Full Name
   - Username
   - Email *(required for account recovery)*
   - Password *(min 8 chars, uppercase, lowercase, number, special char)*
   - Confirm Password
   - Accept Terms & Privacy Policy
4. Click **"Create Account"**
5. Login immediately (no email verification needed)

### Admin Access
- Default admin account can be reset using:
```powershell
.\venv\Scripts\python.exe reset_admin.py
```
- Current reset script credentials are:
   - Username: `admin`
   - Password: `Admin@123`

### Step 4: Explore Features
- **Dashboard**: View real-time air quality data
- **History**: Analyze past readings and trends
- **Forecast**: See 24-hour ML predictions
- **Alerts**: Configure warning thresholds
- **Profile**: Update account settings (add mobile for SMS alerts)

---

## 🔧 System Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for application + data
- **Browser**: Chrome, Firefox, Edge, Safari (latest)

---

## 📁 Project Structure

```
IoT_ML_Project/
├── run.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── reset_admin.py                  # Reset admin credentials
├── ARDUINO_GUIDE.md                # Arduino hardware/setup guide
├── dashboard/
│   └── index.html                  # Main dashboard shell
├── arduino/
│   ├── local_reader/
│   │   └── local_reader.ino        # Arduino local reader sketch
│   ├── test_hardware/
│   │   └── test_hardware.ino       # Hardware test sketch
│   └── thingspeak_logger/
│       └── thingspeak_logger.ino   # ThingSpeak logger sketch
├── data/
│   ├── database/                   # SQLite database
│   │   └── iot_data.db
│   ├── backup/                     # Auto backups
│   └── comprehensive_dataset_15k.csv  # Training data
├── models/
│   ├── air_quality_model.joblib    # Trained ML model
│   ├── scaler.joblib               # Feature scaler
│   └── model_metadata.json         # Model info
├── src/
│   ├── backend/
│   │   ├── core/
│   │   │   └── app.py              # Flask API server
│   │   ├── models/
│   │   │   └── database.py         # Database models
│   │   ├── services/
│   │   │   ├── auth_service.py     # Authentication service
│   │   │   ├── notification_service.py # Twilio/SMS service
│   │   │   └── forecasting_service.py  # ML predictions
│   │   ├── middleware/
│   │   │   └── rate_limiter.py     # API rate limiting
│   │   └── utils/
│   │       ├── logger.py           # Logging helpers
│   │       └── validation.py       # Validation utilities
│   ├── frontend/
│   │   ├── index.html              # Frontend entry page
│   │   ├── css/styles.css          # Styles
│   │   ├── js/app.js               # Core app logic
│   │   ├── js/auth-utils.js        # Auth UI helpers
│   │   └── js/page-templates.js    # Page template rendering
├── scripts/
│   ├── maintenance/
│   │   ├── backup_manager.py       # Backup utilities
│   │   └── scheduled_tasks.py      # Scheduled cleanup/backups
│   └── ml/
│       └── train_model.py          # Model training script
└── venv/                           # Virtual environment
```

---

## 🔐 Security Features

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)
- Not a common password

### Session Security
- CSRF protection
- Secure session cookies
- HTTP security headers (X-Frame-Options, CSP, HSTS)
- Device fingerprinting
- IP address tracking
- User agent validation

### Rate Limiting
- **Login**: 5 attempts per 15 minutes
- **Registration**: 3 attempts per 15 minutes
- **API calls**: 100 requests per minute
- Auto-lockout: 15 minutes after threshold exceeded

---

## 💻 Hardware Setup (Optional)

### Arduino with Sensors

**Components:**
- Arduino Uno/Mega
- MQ-135 Air Quality Sensor
- DHT11 Temperature/Humidity Sensor
- Jumper wires
- Breadboard (optional)

**Connections:**
- MQ-135 Analog Output → Arduino A0
- DHT11 Data Pin → Arduino Pin 2
- Both sensors: VCC to 5V, GND to GND

**Upload Code:**
1. Open Arduino IDE
2. Load `src/arduino/local_reader/local_reader.ino`
3. Select correct board and COM port
4. Upload to Arduino
5. Open Serial Monitor (9600 baud)
6. Data will stream to the web server

### Using Generated Data (No Hardware)

The system automatically generates realistic sensor data if no Arduino is connected. Perfect for:
- Testing the application
- Development without hardware
- Demonstrating ML predictions
- Learning the system

---

## 🤖 Machine Learning Model

### Training Data
- **15,000+ samples** from multiple sources
- **Features**: Temperature, Humidity, MQ-135 readings, Time of day, Day of week
- **Target**: AQI categories (Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous)

### Model Performance
- **Algorithm**: Random Forest Classifier
- **Accuracy**: 95%+
- **Cross-Validation**: 5-fold CV
- **Feature Importance**: 
  - MQ-135 sensor: 50%
  - Temperature: 30%
  - Humidity: 20%

### Retrain Model
```powershell
python scripts/ml/train_model.py
```

This will:
- Load training data from `data/comprehensive_dataset_15k.csv`
- Train new Random Forest model
- Save model to `models/air_quality_model.joblib`
- Generate performance metrics

---

## 📱 Mobile Alert Setup (Optional)

Mobile alerts are **optional** and configured from the **Admin** panel.

### Setup Steps
1. Login as admin (`admin`)
2. Open **Admin** page
3. In **Mobile Notification Setup**, enter:
   - Twilio Account SID (`AC...`)
   - Twilio Auth Token
   - Twilio phone number (`+1234567890` format)
   - Optional WhatsApp sender number
   - Admin mobile number (target for test alert)
4. Click **Save Configuration**
5. Click **Test Connection**

Important:
- Use credentials from the **same Twilio account/project**.
- Use a consistent app URL (`http://localhost:5000`) when logging in and saving settings.

### Requirements
- Twilio account (for SMS)
- WhatsApp Business API (for WhatsApp)

**Configuration Source**:
- Credentials are stored in database settings and loaded by `src/backend/services/notification_service.py`.

**Twilio Authentication Method**:
```python
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = '+your_twilio_number'
```

---

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/status` - Check session status
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/login-history` - View login history
- `GET /api/auth/sessions` - View active sessions

### Data & Monitoring
- `GET /api/readings` - Get sensor readings (with pagination)
- `POST /api/readings` - Add new reading (from Arduino)
- `GET /api/readings/latest` - Get most recent reading
- `GET /api/forecast` - Get 24-hour predictions
- `GET /api/settings` - Get user settings
- `POST /api/settings` - Update settings

### Alerts
- `GET /api/alerts` - Get all alerts
- `POST /api/alerts` - Create new alert rule
- `PUT /api/alerts/<id>` - Update alert rule
- `DELETE /api/alerts/<id>` - Delete alert rule

### System
- `GET /api/system/stats` - System statistics
- `POST /api/backup` - Create manual backup
- `GET /api/export/csv` - Export data as CSV

---

## 🛠 Troubleshooting

### Server Won't Start
```powershell
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill the process using port 5000
Stop-Process -Id <PID> -Force

# Or use a different port
$env:FLASK_RUN_PORT=5001
python run.py
```

### Database Errors
```powershell
# Delete and recreate database
Remove-Item data\database\iot_data.db
python run.py  # Will recreate with correct schema
```

### Module Import Errors
```powershell
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# Or use virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Arduino Connection Issues
- Check COM port in Arduino IDE Tools > Port
- Verify baud rate is 9600
- Install CH340 or FTDI drivers if needed
- Test sensors with Serial Monitor first

### Password Reset Lost
```powershell
# Reset admin credentials quickly
.\venv\Scripts\python.exe reset_admin.py
```

---

## 🎓 Learning Outcomes

This project demonstrates:
- **IoT Integration**: Sensor data collection from Arduino/ESP32
- **Machine Learning**: Model training, deployment, and predictions
- **Web Development**: Flask backend + Bootstrap frontend
- **Authentication**: Professional user management and security
- **Real-time Data**: WebSocket-style updates and live charts
- **Database Design**: SQLAlchemy ORM with complex relationships
- **API Development**: RESTful API design and documentation
- **Security**: Password hashing, session management, rate limiting
- **DevOps**: Automated backups, logging, scheduled tasks

---

## 📝 Configuration Files

### Environment Variables (Optional)
Create `.env` file for sensitive data:
```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///data/database/iot_data.db
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Database Configuration
Edit `src/backend/core/app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///path/to/custom.db'
app.config['SECRET_KEY'] = 'change-this-in-production'
```

### Session Settings
```python
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Fork and modify
- Add new features
- Improve ML models
- Enhance UI/UX
- Fix bugs
- Write documentation

### Development Setup
```powershell
# Clone repository
git clone <your-repo-url>
cd IoT_ML_Project

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run in development mode
$env:FLASK_ENV=development
python run.py
```

---

## 📄 License

This project is for educational purposes. Use freely for learning and development.

**No warranty provided**. Use at your own risk.

---

## 📞 Support

### Common Issues
1. **"Port already in use"** → Kill process or change port
2. **"Module not found"** → Reinstall requirements.txt
3. **"Database locked"** → Close other connections
4. **"Cannot import name"** → Check Python version (3.8+)

### Debug Mode
```powershell
$env:FLASK_ENV=development
$env:FLASK_DEBUG=1
python run.py
```

This enables:
- Detailed error pages
- Auto-reload on code changes
- Enhanced logging

---

## 🏆 Project Highlights

### Professional Features
✅ Enterprise-grade authentication system  
✅ Real-time machine learning predictions  
✅ Responsive mobile-friendly dashboard  
✅ Automated database backups  
✅ Rate limiting and security headers  
✅ Session management with device tracking  
✅ Multi-channel notifications (SMS/WhatsApp)  
✅ Login history and audit logs  
✅ Password strength enforcement  
✅ Account lockout protection  

### Technology Stack
- **Backend**: Python 3.8+, Flask, SQLAlchemy, scikit-learn
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JavaScript
- **Database**: SQLite with WAL mode
- **ML**: Random Forest, feature engineering, cross-validation
- **Hardware**: Arduino/ESP32, MQ-135, DHT11
- **Security**: bcrypt, CSRF tokens, rate limiting

---

## 📚 Documentation

- **README.md** (this file) - Complete setup guide
- **ARDUINO_GUIDE.md** - Arduino hardware and upload guide
- Inline code comments - Detailed function documentation

---

## 🔄 Version History

**Version 2.0** - February 2026
- Professional authentication system
- Simplified registration (email-based)
- Enhanced security features
- Session management
- Login history tracking
- Password strength checker
- Remember me functionality

**Version 1.0** - Initial Release
- Basic authentication
- Real-time monitoring
- ML predictions
- Alert system

---

## 📈 Future Enhancements

**Planned Features:**
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced ML models (LSTM, Transformer)
- [ ] Real-time WebSocket updates
- [ ] Map view for multiple devices
- [ ] Weather API integration
- [ ] Historical trend analysis
- [ ] Role-based access control (Admin/User)
- [ ] Two-factor authentication
- [ ] Export to PDF reports

---

**Built with ❤️ using Python, Flask, scikit-learn, and Arduino**

**Version**: 2.2 (Auth Token Authentication Update)  
**Last Updated**: March 17, 2026

For questions or issues, check the troubleshooting section or review the code comments.

