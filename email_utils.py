import os
import random
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(receiver_email, otp):

    sender = {
        "name": "Finance Tracker",
        "email": os.getenv("EMAIL_ADDRESS")
    }

    email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,
        to=[{"email": receiver_email}],
        subject="Your Finance Tracker OTP",
        html_content=f"""
        <h2>Finance Tracker</h2>
        <p>Your OTP is:</p>
        <h1>{otp}</h1>
        <p>This OTP is valid for 10 minutes.</p>
        """
    )

    print("=" * 50)
    print("BREVO DEBUG")
    print("Sender :", sender["email"])
    print("Receiver :", receiver_email)
    print("OTP :", otp)

    try:
        response = api_instance.send_transac_email(email)
        print("SUCCESS:", response)
        return True

    except ApiException as e:
        print("FAILED:", e)
        return False