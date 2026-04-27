import os
from dotenv import load_dotenv
from courier import Courier

load_dotenv()


def send_password_reset_email(email, first_name, reset_link):
    """
    Sends a password reset email via Courier.
    """
    try:
        client = Courier(api_key=os.getenv("COURIER_AUTH_KEY"))
        response = client.send(
            message={
                "to": {
                    "email": email,
                },
                "content": {
                    "title": "HealthPlus - Password Reset Request",
                    "body": (
                        f"Hi {first_name},\n\n"
                        "We received a request to reset your HealthPlus password.\n\n"
                        f"Click the link below to reset your password:\n{reset_link}\n\n"
                        "This link will expire in 1 hour.\n\n"
                        "If you didn't request a password reset, you can safely ignore this email."
                    ),
                },
            }
        )
        print(f"Password reset email sent! Request ID: {response.request_id}")
        return response
    except Exception as e:
        print(f"Courier SDK Error (password reset): {e}")
        return None
