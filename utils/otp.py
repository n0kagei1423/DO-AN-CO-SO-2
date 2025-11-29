import smtplib
import ssl
import random
import socket
from email.message import EmailMessage

from dotenv import load_dotenv
import os

load_dotenv('./database/env/.env')

EMAIL_SENDER = os.getenv("MAIL")
EMAIL_PASSWORD = os.getenv("PASS")

def sinh_ma_otp():
    return str(random.randint(100000, 999999))

def gui_otp_qua_email(email_nhan, ma_otp):
    msg = EmailMessage()
    msg.set_content(f"Ma OTP cua ban la: {ma_otp}")
    msg['Subject'] = "SpeedTest OTP"
    msg['From'] = EMAIL_SENDER
    msg['To'] = email_nhan

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
        return True
    
    except socket.timeout:
        print("Lỗi: Hết thời gian chờ (Timeout). Mạng quá chậm.")
        return False
    
    except Exception as e:
        print(f"Lỗi: {e}")
        return False