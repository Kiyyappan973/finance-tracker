import os
from dotenv import load_dotenv
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

sender = {"name": "Finance Tracker", "email": os.getenv("EMAIL_ADDRESS")}
to = [{"email": os.getenv("EMAIL_ADDRESS")}]  # sending to yourself as a test

send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
    to=to,
    sender=sender,
    subject="Test Email",
    html_content="<p>This is a test</p>"
)

try:
    response = api_instance.send_transac_email(send_smtp_email)
    print("SUCCESS:", response)
except ApiException as e:
    print("FAILED:", e)