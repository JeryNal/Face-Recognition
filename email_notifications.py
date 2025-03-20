from flask_mail import Message
import logging
import random
import string

def generate_otp(length=6):
    """Generate a numeric OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_login_notification(mail, recipient_email, user_name, login_time, ip_address=None):
    """
    Send an email notification when a user logs in
    
    Args:
        mail: Flask-Mail instance
        recipient_email: Email address to send notification to
        user_name: Name of the user who logged in
        login_time: Timestamp of the login
        ip_address: IP address of the login request (optional)
    """
    try:
        subject = "Login Notification - Face Recognition System"
        
        # Create message content
        body = f"""
        Hello {user_name},
        
        We detected a new login to your account at {login_time}.
        """
        
        if ip_address:
            body += f"\nIP Address: {ip_address}"
            
        body += """
        
        If this was you, you can ignore this message. If you didn't log in, please change your password immediately.
        
        Regards,
        Face Recognition System
        """
        
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            sender="noreply@facerecognition.app"
        )
        
        mail.send(msg)
        logging.info(f"Login notification email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send login notification email: {str(e)}")
        return False

def send_registration_confirmation(mail, recipient_email, user_name, registration_time):
    """
    Send a confirmation email when a user registers
    
    Args:
        mail: Flask-Mail instance
        recipient_email: Email address to send notification to
        user_name: Name of the user who registered
        registration_time: Timestamp of the registration
    """
    try:
        subject = "Welcome to Face Recognition System"
        
        # Create message content
        body = f"""
        Hello {user_name},
        
        Thank you for registering with our Face Recognition System at {registration_time}.
        
        Your account has been successfully created. You can now log in and use our facial recognition features.
        
        To complete your setup, please log in and register your face for facial recognition.
        
        Welcome aboard!
        
        Regards,
        Face Recognition System Team
        """
        
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            sender="noreply@facerecognition.app"
        )
        
        mail.send(msg)
        logging.info(f"Registration confirmation email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send registration confirmation email: {str(e)}")
        return False

def send_otp_email(mail, recipient_email, user_name, otp):
    """
    Send an OTP verification email for registration
    
    Args:
        mail: Flask-Mail instance
        recipient_email: Email address to send OTP to
        user_name: Name of the user
        otp: The generated OTP code
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    try:
        subject = "Email Verification Code - Face Recognition System"
        
        # Create message content
        body = f"""
        Hello {user_name},
        
        Your verification code for Face Recognition System is: {otp}
        
        Please enter this code on the verification page to complete your registration.
        This code will expire in 10 minutes.
        
        If you did not request this code, please ignore this email.
        
        Regards,
        Face Recognition System Team
        """
        
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            sender="noreply@facerecognition.app"
        )
        
        mail.send(msg)
        logging.info(f"OTP verification email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send OTP verification email: {str(e)}")
        return False 