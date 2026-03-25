"""
Mobile Notification Service
Sends SMS and WhatsApp notifications using Twilio
Replaces email service with mobile-first notifications
"""

import os
import json
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class MobileNotificationService:
    """
    Mobile notification service supporting SMS and WhatsApp
    Uses Twilio API for message delivery
    """
    
    def __init__(self, account_sid='', auth_token='', from_number='', whatsapp_from=''):
        """
        Initialize mobile notification service using Twilio Auth Token authentication
        
        Args:
            account_sid: Twilio Account SID (required, starts with 'AC')
            auth_token: Twilio Auth Token (required, 32 characters)
            from_number: Twilio phone number for SMS (e.g., '+1234567890')
            whatsapp_from: Twilio WhatsApp number (e.g., 'whatsapp:+14155238886')
        """
        # Strip whitespace from all credentials
        self.account_sid = account_sid.strip() if account_sid else ''
        self.auth_token = auth_token.strip() if auth_token else ''
        self.from_number = from_number.strip() if from_number else ''
        self.whatsapp_from = whatsapp_from.strip() if whatsapp_from else ''

        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        
        print("="*60)
        print("MOBILE NOTIFICATION SERVICE INITIALIZATION")
        print("="*60)
        print("Authentication Method: Auth Token")
        
        if self.account_sid:
            print(f"Account SID: Present ({self.account_sid[:10]}...), length: {len(self.account_sid)}")
        else:
            print("Account SID: MISSING")
        
        if self.auth_token:
            print(f"Auth Token: Present ({'*' * 20}), length: {len(self.auth_token)}")
        else:
            print("Auth Token: MISSING")
            
        print(f"Phone Number: {self.from_number if self.from_number else 'MISSING'}")
        print(f"WhatsApp: {self.whatsapp_from if self.whatsapp_from else 'Not configured'}")
        print(f"Enabled: {self.enabled}")
        
        # Validate credential formats
        if self.account_sid:
            if not self.account_sid.startswith('AC'):
                print("⚠️  WARNING: Account SID should start with 'AC'")
            if len(self.account_sid) != 34:
                print(f"⚠️  WARNING: Account SID should be 34 characters (got {len(self.account_sid)})")
        
        if self.auth_token:
            if len(self.auth_token) != 32:
                print(f"⚠️  WARNING: Auth Token is usually 32 characters (got {len(self.auth_token)})")
        
        if self.from_number:
            if not self.from_number.startswith('+'):
                print("⚠️  WARNING: Phone number should start with '+' (E.164 format)")
        
        if self.enabled:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("✓ Twilio client created successfully (Auth Token authentication)")
                print("="*60)
            except Exception as e:
                print(f"✗ Failed to create Twilio client: {e}")
                print("="*60)
                self.enabled = False
                self.client = None
        else:
            self.client = None
            print("⚠️  Mobile notification service not configured (missing credentials)")
            print("="*60)
    
    def send_sms(self, to_number, message):
        """
        Send SMS notification
        
        Args:
            to_number: Recipient phone number (E.164 format: +1234567890)
            message: Text message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"⚠️  SMS not configured. Would send to {to_number}: {message}")
            return False
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            print(f"✅ SMS sent to {to_number} (SID: {message_obj.sid})")
            return True
        except TwilioRestException as e:
            print(f"❌ SMS failed: {e.msg}")
            return False
        except Exception as e:
            print(f"❌ SMS error: {str(e)}")
            return False
    
    def send_whatsapp(self, to_number, message):
        """
        Send WhatsApp notification
        
        Args:
            to_number: Recipient WhatsApp number (format: 'whatsapp:+1234567890')
            message: Text message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled or not self.whatsapp_from:
            print(f"⚠️  WhatsApp not configured. Would send to {to_number}: {message}")
            return False
        
        # Ensure proper WhatsApp prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.whatsapp_from,
                to=to_number
            )
            print(f"✅ WhatsApp sent to {to_number} (SID: {message_obj.sid})")
            return True
        except TwilioRestException as e:
            print(f"❌ WhatsApp failed: {e.msg}")
            return False
        except Exception as e:
            print(f"❌ WhatsApp error: {str(e)}")
            return False
    
    def send_aqi_alert(self, to_number, aqi, level, message, device_name='Unknown', location='Unknown', 
                       notification_type='sms'):
        """
        Send AQI alert via SMS or WhatsApp
        
        Args:
            to_number: Recipient phone number
            aqi: Current AQI value
            level: Alert level (warning, danger, critical)
            message: Alert message
            device_name: Name of the device
            location: Device location
            notification_type: 'sms' or 'whatsapp'
        
        Returns:
            bool: True if sent successfully
        """
        # Format alert message
        alert_text = f"""
🚨 AIR QUALITY ALERT 🚨

Level: {level.upper()}
AQI: {aqi:.1f}

{message}

Device: {device_name}
Location: {location}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Recommended Actions:
• Close windows and doors
• Use air purifiers
• Limit outdoor activities
• Monitor sensitive individuals

IoT Air Quality Monitor
""".strip()
        
        channel = (notification_type or 'sms').lower()

        if channel == 'both':
            sms_ok = self.send_sms(to_number, alert_text)
            whatsapp_ok = self.send_whatsapp(to_number, alert_text)
            # Consider alert sent if either channel succeeds.
            return sms_ok or whatsapp_ok

        if channel == 'whatsapp':
            # Fallback to SMS when WhatsApp sender is not configured.
            whatsapp_ok = self.send_whatsapp(to_number, alert_text)
            if not whatsapp_ok:
                return self.send_sms(to_number, alert_text)
            return True

        return self.send_sms(to_number, alert_text)
    
    def send_otp(self, to_number, otp_code, notification_type='sms'):
        """
        Send OTP verification code
        
        Args:
            to_number: Recipient phone number
            otp_code: 6-digit OTP code
            notification_type: 'sms' or 'whatsapp'
        
        Returns:
            bool: True if sent successfully
        """
        message = f"""
Your IoT Air Quality Monitor verification code is:

{otp_code}

This code will expire in 10 minutes.
Do not share this code with anyone.

If you didn't request this code, please ignore this message.
""".strip()
        
        if notification_type == 'whatsapp':
            return self.send_whatsapp(to_number, message)
        else:
            return self.send_sms(to_number, message)
    
    def send_password_reset(self, to_number, reset_code, notification_type='sms'):
        """
        Send password reset code
        
        Args:
            to_number: Recipient phone number
            reset_code: 6-digit reset code
            notification_type: 'sms' or 'whatsapp'
        
        Returns:
            bool: True if sent successfully
        """
        message = f"""
IoT Air Quality Monitor - Password Reset

Your password reset code is:

{reset_code}

This code will expire in 30 minutes.

If you didn't request a password reset, please ignore this message and ensure your account is secure.
""".strip()
        
        if notification_type == 'whatsapp':
            return self.send_whatsapp(to_number, message)
        else:
            return self.send_sms(to_number, message)
    
    def send_account_notification(self, to_number, title, message, notification_type='sms'):
        """
        Send general account notification
        
        Args:
            to_number: Recipient phone number
            title: Notification title
            message: Notification content
            notification_type: 'sms' or 'whatsapp'
        
        Returns:
            bool: True if sent successfully
        """
        full_message = f"""
IoT Air Quality Monitor

{title}

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
        
        if notification_type == 'whatsapp':
            return self.send_whatsapp(to_number, full_message)
        else:
            return self.send_sms(to_number, full_message)
    
    def test_connection(self, test_phone_number=None):
        """
        Test Twilio connection by sending test SMS
        
        Args:
            test_phone_number: Phone number to send test SMS (E.164 format)
        
        Returns:
            dict: Connection status and details
        """
        print("="*60)
        print("TESTING TWILIO CONNECTION")
        print("="*60)
        
        if not self.enabled:
            error = 'Mobile notification service not configured. Please add Twilio credentials.'
            print(f"✗ {error}")
            print("="*60)
            return {
                'success': False,
                'error': error
            }
        
        if not self.client:
            error = 'Twilio client not initialized'
            print(f"✗ {error}")
            print("="*60)
            return {
                'success': False,
                'error': error
            }
        
        try:
            # First verify account credentials
            print(f"Account SID: {self.account_sid[:10]}...{self.account_sid[-4:]}")
            print(f"From Number: {self.from_number}")
            print(f"Testing authentication...")
            
            account = self.client.api.accounts(self.account_sid).fetch()
            print(f"✓ Account verified: {account.friendly_name}")
            print(f"✓ Account status: {account.status}")
            
            # If test number provided, send actual test SMS
            if test_phone_number:
                test_phone_number = test_phone_number.strip()
                print(f"\nSending test SMS...")
                print(f"From: {self.from_number}")
                print(f"To: {test_phone_number}")
                
                message_obj = self.client.messages.create(
                    body="✓ SUCCESS! Twilio is configured correctly. IoT Air Quality Monitoring System is ready to send alerts.",
                    from_=self.from_number,
                    to=test_phone_number
                )
                
                print(f"\n✓ TEST SMS SENT SUCCESSFULLY!")
                print(f"Message SID: {message_obj.sid}")
                print(f"Status: {message_obj.status}")
                print(f"Direction: {message_obj.direction}")
                print("="*60)
                
                return {
                    'success': True,
                    'message': f'✓ Test SMS sent successfully! Check {test_phone_number} for the message.',
                    'account': account.friendly_name,
                    'status': account.status,
                    'message_sid': message_obj.sid
                }
            else:
                print("="*60)
                return {
                    'success': True,
                    'message': f'Twilio account verified: {account.friendly_name}',
                    'account': account.friendly_name,
                    'status': account.status
                }
                
        except TwilioRestException as e:
            print(f"\n✗ TWILIO ERROR")
            print(f"Code: {e.code}")
            print(f"Message: {e.msg}")
            print(f"Status: {e.status}")
            
            # Provide helpful error messages
            if e.code == 20003:
                error_msg = "Authentication failed. Your Account SID or Auth Token is incorrect. Please re-enter them carefully in Admin Panel."
                
            elif e.code == 21211:
                error_msg = f"Invalid 'To' phone number: {test_phone_number}. Format should be: +[country code][number] (e.g., +12025551234)"
                
            elif e.code == 21608:
                error_msg = f"Phone number {test_phone_number} is not verified.\n\n" + \
                          f"TRIAL ACCOUNT LIMITATION: You must verify this number first.\n" + \
                          f"Steps:\n" + \
                          f"1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified\n" + \
                          f"2. Click '+ Add a new number'\n" + \
                          f"3. Enter {test_phone_number}\n" + \
                          f"4. Verify the SMS code you receive"
                
            elif e.code == 21614:
                error_msg = f"Invalid 'From' phone number: {self.from_number}. Please check your Twilio phone number in Admin Panel."
                
            elif e.code == 21606:
                error_msg = f"{test_phone_number} is not a valid mobile number (might be a landline)"
                
            else:
                error_msg = f"Twilio Error {e.code}: {e.msg}"
            
            print(f"Error: {error_msg}")
            print("="*60)
            
            return {
                'success': False,
                'error': error_msg,
                'code': e.code
            }
            
        except Exception as e:
            print(f"\n✗ UNEXPECTED ERROR")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            print("="*60)
            
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
            
            return {
                'success': False,
                'error': error_msg,
                'code': e.code
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"✗ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
