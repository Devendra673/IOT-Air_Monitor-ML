"""
IoT Air Quality Monitoring System - Startup Script
Run this file to start the web server and dashboard
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'src' / 'backend'
sys.path.insert(0, str(backend_path))

# Import and run the app from new structure
from core.app import app, db, initialize_database, load_ml_model, logger

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  IoT Air Quality Monitoring System")
    print("="*50 + "\n")
    
    # Load ML model first
    logger.info("Loading ML model...")
    if not load_ml_model():
        print("⚠️  WARNING: ML model failed to load!")
        print("   Prediction features will not work.")
        print("   Run: python src/backend/train_model.py")
    else:
        print("✓ ML model loaded successfully")
    
    # Initialize database
    logger.info("Initializing database...")
    with app.app_context():
        initialize_database()
    
    print("✓ Database initialized")
    print("✓ Starting Flask server...")
    print(f"✓ Dashboard: http://localhost:5000")
    print(f"✓ Default login: admin / admin123")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
