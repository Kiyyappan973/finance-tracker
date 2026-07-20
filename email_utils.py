import random
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(receiver_email, otp):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {"name": "Finance Tracker", "email": os.getenv("EMAIL_ADDRESS")}
    to = [{"email": receiver_email}]
    subject = "Your Finance Tracker Verification Code"
    html_content = f"<p>Your OTP code is: <strong>{otp}</strong></p><p>This code will expire in 10 minutes.</p>"

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
    response = api_instance.send_transac_email(send_smtp_email)
    print("EMAIL SENT SUCCESSFULLY:", response, flush=True)
except ApiException as e:
     print("EMAIL SENDING FAILED:", e, flush=True)