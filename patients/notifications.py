import os
from dotenv import load_dotenv
from courier import Courier
# Load the .env file to get your keys
load_dotenv()

# Initialize the Courier client
client = Courier(api_key=os.getenv("COURIER_AUTH_KEY"))

def notify_patient(profile, title, content, doctor_name):
    """
    Sends the notification using the Courier SDK v7.x syntax.
    """
    try:
        response = client.send(
            message={
                "to": {
                    "email": profile.email,
                    "phone_number": profile.phone_number,
                },
                "template": os.getenv("COURIER_TEMPLATE_ID"),
                "data": {
                    "patient_name": profile.first_name,
                    "doctor_name": doctor_name,
                    "update_text": content,
                    "alert_title": title,
                    "frequency": profile.notification_frequency,
                },
                "routing": {
                    "method": "single",
                    "channels": ["email", "sms"],
                },
            }
        )
        print(f"Sent! Request ID: {response.request_id}")
        return response
    except Exception as e:
        print(f"Courier SDK Error: {e}")
        return None