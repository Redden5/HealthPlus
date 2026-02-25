from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
import re


class StrongPasswordValidator:
    def validate(self, password, user=None):
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain an uppercase letter.')
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain a lowercase letter.')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain a number.')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
            raise ValidationError('Password must contain a special character.')

    def get_help_text(self):
        return 'Password must include uppercase, lowercase, number, and special character.'


def validate_profile_setup(post_data):
    """
    Validates profile setup form data.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Required fields
    required_fields = {
        'first_name': 'First name is required.',
        'last_name': 'Last name is required.',
        'email': 'Email address is required.',
        'phone': 'Phone number is required.',
        'date_of_birth': 'Date of birth is required.',
    }

    for field, message in required_fields.items():
        if not post_data.get(field, '').strip():
            errors.append(message)

    # Name fields — letters, spaces, hyphens, apostrophes only
    name_pattern = re.compile(r"^[a-zA-Z\s\-']+$")
    first_name = post_data.get('first_name', '').strip()
    last_name = post_data.get('last_name', '').strip()

    if first_name and not name_pattern.match(first_name):
        errors.append('First name can only contain letters, spaces, hyphens, and apostrophes.')
    if last_name and not name_pattern.match(last_name):
        errors.append('Last name can only contain letters, spaces, hyphens, and apostrophes.')

    # Phone must be 10 digits
    phone = ''.join(c for c in post_data.get('phone', '') if c.isdigit())
    if phone and len(phone) != 10:
        errors.append('Phone number must be 10 digits.')

    # Weight must be a number between 1-999
    weight = post_data.get('weight', '').strip()
    if weight:
        if not weight.isdigit() or not (1 <= int(weight) <= 999):
            errors.append('Weight must be a number between 1 and 999.')

    # Email format
    email = post_data.get('email', '').strip()
    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Please enter a valid email address.')

    # Password validation
    password = post_data.get('password')
    confirm_password = post_data.get('confirm_password')

    if not password:
        errors.append('Password is required.')
    elif password != confirm_password:
        errors.append('Passwords do not match.')
    else:
        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)

    # Terms checkbox
    if not post_data.get('terms_agreed'):
        errors.append('You must agree to the terms to continue.')

    return errors