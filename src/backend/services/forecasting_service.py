"""
AQI Forecasting Module
Uses LSTM/time series analysis to predict future AQI values
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from sklearn.preprocessing import MinMaxScaler
import pickle
from pathlib import Path

class AQIForecaster:
    """Simple time-series forecaster for AQI predictions"""
    
    def __init__(self):
        self.history = deque(maxlen=100)  # Store last 100 readings
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.trained = False
        self.min_history_size = 20  # Minimum readings needed for forecasting
    
    def add_reading(self, timestamp, aqi, temperature, humidity):
        """Add new reading to history"""
        self.history.append({
            'timestamp': timestamp,
            'aqi': aqi,
            'temperature': temperature,
            'humidity': humidity
        })
    
    def can_forecast(self):
        """Check if we have enough data to forecast"""
        return len(self.history) >= self.min_history_size
    
    def forecast_simple(self, hours=1):
        """
        Simple forecasting using moving average and trend analysis
        More sophisticated than just averaging - considers recent trends
        """
        if not self.can_forecast():
            return {
                'success': False,
                'error': f'Need at least {self.min_history_size} readings for forecasting'
            }
        
        try:
            # Convert history to dataframe
            df = pd.DataFrame(list(self.history))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculate trend (slope of last 10 readings)
            recent_aqi = df['aqi'].tail(10).values
            x = np.arange(len(recent_aqi))
            slope = np.polyfit(x, recent_aqi, 1)[0]
            
            # Calculate moving averages
            ma_5 = df['aqi'].tail(5).mean()
            ma_10 = df['aqi'].tail(10).mean()
            current_aqi = df['aqi'].iloc[-1]
            
            # Weight recent readings more heavily
            weights = np.exp(np.linspace(-1, 0, len(recent_aqi)))
            weights /= weights.sum()
            weighted_avg = np.sum(recent_aqi * weights)
            
            # Forecast based on trend and weighted average
            forecast_values = []
            for hour in range(1, hours + 1):
                # Base forecast on weighted average + trend
                forecast = weighted_avg + (slope * hour * 6)  # 6 = 10-min readings per hour
                
                # Add seasonal/time-of-day adjustment
                forecast_time = df['timestamp'].iloc[-1] + timedelta(hours=hour)
                hour_of_day = forecast_time.hour
                
                # Simple time-of-day adjustment (peak pollution during day)
                if 6 <= hour_of_day <= 10:  # Morning rush
                    forecast *= 1.1
                elif 18 <= hour_of_day <= 21:  # Evening rush
                    forecast *= 1.05
                elif 0 <= hour_of_day <= 5:  # Night
                    forecast *= 0.95
                
                # Clamp to reasonable range
                forecast = max(0, min(500, forecast))
                
                forecast_values.append({
                    'hour': hour,
                    'timestamp': forecast_time.isoformat(),
                    'aqi': round(forecast, 1),
                    'confidence': self._calculate_confidence(hour)
                })
            
            # Calculate trend direction
            if slope > 0.5:
                trend = 'Worsening'
                trend_icon = '📈'
            elif slope < -0.5:
                trend = 'Improving'
                trend_icon = '📉'
            else:
                trend = 'Stable'
                trend_icon = '➡️'
            
            return {
                'success': True,
                'current_aqi': round(current_aqi, 1),
                'forecasts': forecast_values,
                'trend': trend,
                'trend_icon': trend_icon,
                'slope': round(slope, 3),
                'confidence': self._calculate_confidence(1),
                'data_points': len(self.history),
                'method': 'Weighted Moving Average + Trend Analysis'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Forecast error: {str(e)}'
            }
    
    def _calculate_confidence(self, hours_ahead):
        """Calculate confidence level for forecast"""
        # Confidence decreases with time
        base_confidence = min(95, len(self.history))
        decay = 5 * hours_ahead  # 5% decrease per hour
        confidence = max(50, base_confidence - decay)
        return round(confidence, 0)
    
    def get_statistics(self):
        """Get statistics from historical data"""
        if len(self.history) == 0:
            return None
        
        df = pd.DataFrame(list(self.history))
        
        return {
            'mean_aqi': round(df['aqi'].mean(), 1),
            'max_aqi': round(df['aqi'].max(), 1),
            'min_aqi': round(df['aqi'].min(), 1),
            'std_aqi': round(df['aqi'].std(), 1),
            'readings': len(self.history),
            'latest_aqi': round(df['aqi'].iloc[-1], 1)
        }
    
    def save_state(self, filepath):
        """Save forecaster state to file"""
        state = {
            'history': list(self.history),
            'trained': self.trained
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
    
    def load_state(self, filepath):
        """Load forecaster state from file"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            self.history = deque(state['history'], maxlen=100)
            self.trained = state['trained']
            return True
        except:
            return False

# Global forecaster instance
forecaster = AQIForecaster()
