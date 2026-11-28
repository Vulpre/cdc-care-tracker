"""
Email verification with one-time codes (OTP).

A new account is created inactive. `send_code` emails a 6-digit code;
`check_code` activates the account when the right code is entered.
"""
import math
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from MyNewApp.models import EmailVerification

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5

# Results of check_code
OK, WRONG, EXPIRED, TOO_MANY, MISSING = 'ok', 'wrong', 'expired', 'too_many', 'missing'


def _hash(user, code):
    # Keyed with SECRET_KEY and bound to the user, so a leaked table is useless.
    return salted_hmac('email-otp', f'{user.pk}:{code}').hexdigest()


def seconds_until_resend(user):
    """0 when a new code may be sent, otherwise the seconds left to wait."""
    v = EmailVerification.objects.filter(user=user).first()
    if not v:
        return 0
    left = (v.created_at + RESEND_COOLDOWN - timezone.now()).total_seconds()
    return max(0, math.ceil(left))


def send_code(user):
    """Create a fresh code (replacing any old one) and email it."""
    code = f'{secrets.randbelow(1_000_000):06d}'
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={'code_hash': _hash(user, code), 'created_at': timezone.now(), 'attempts': 0},
    )
    minutes = int(CODE_TTL.total_seconds() // 60)
    send_mail(
        subject=f'{code} is your CDC Care Tracker verification code',
        message=(
            f'Hi {user.first_name or user.username},\n\n'
            f'Your verification code is: {code}\n\n'
            f'Enter it on the verification page to finish creating your account. '
            f'The code expires in {minutes} minutes.\n\n'
            f"If you didn't create an account, you can ignore this email.\n\n"
            f'— CDC Care Tracker'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def check_code(user, code):
    """Check a submitted code. On success, activate the user and drop the code."""
    v = EmailVerification.objects.filter(user=user).first()
    if not v:
        return MISSING
    if v.attempts >= MAX_ATTEMPTS:
        return TOO_MANY
    if timezone.now() > v.created_at + CODE_TTL:
        return EXPIRED

    if not constant_time_compare(v.code_hash, _hash(user, code)):
        v.attempts += 1
        v.save(update_fields=['attempts'])
        return TOO_MANY if v.attempts >= MAX_ATTEMPTS else WRONG

    user.is_active = True
    user.save(update_fields=['is_active'])
    v.delete()
    return OK


def mask_email(email):
    """maria.santos@gmail.com -> m***s@gmail.com"""
    local, _, domain = email.partition('@')
    if len(local) <= 2:
        return f'{local[:1]}***@{domain}'
    return f'{local[0]}***{local[-1]}@{domain}'
