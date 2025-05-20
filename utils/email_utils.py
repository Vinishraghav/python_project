import random
import string
from datetime import datetime, timedelta

# Store OTPs in memory (in a real app, this would be in a database)
otp_store = {}

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def store_otp(email, otp):
    """Store OTP with expiration time (10 minutes)"""
    expiry = datetime.now() + timedelta(minutes=10)
    otp_store[email] = {
        'otp': otp,
        'expiry': expiry
    }
    print(f"OTP stored for {email}: {otp} (expires at {expiry})")
    return otp

def verify_otp(email, otp):
    """Verify if OTP is valid and not expired"""
    print(f"Verifying OTP for {email}: {otp}")
    print(f"Current OTP store: {otp_store}")

    if email not in otp_store:
        print(f"No OTP found for {email}")
        return False

    stored_data = otp_store[email]
    if datetime.now() > stored_data['expiry']:
        # OTP expired, remove it
        print(f"OTP expired for {email}")
        del otp_store[email]
        return False

    if stored_data['otp'] == otp:
        # OTP verified, remove it
        print(f"OTP verified for {email}")
        del otp_store[email]
        return True

    print(f"Invalid OTP for {email}: expected {stored_data['otp']}, got {otp}")
    return False

def send_otp_email(recipient_email, otp):
    """Send OTP to user's email (simulated)"""
    print(f"\n==== EMAIL NOTIFICATION ====")
    print(f"To: {recipient_email}")
    print(f"Subject: Your Tour Van Booking Verification Code")
    print(f"Body: Your verification code is: {otp}")
    print(f"This code will expire in 10 minutes.")
    print(f"==========================\n")

    # For demo, always return success
    return True
