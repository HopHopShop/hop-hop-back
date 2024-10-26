import os

from django.core.mail import send_mail


def send_reset_password_email(token, email):
    reset_url = f"{os.environ['BASE_URL']}{os.environ['PASSWORD_RESET_PATH']}?key={token}&user_email={email}"

    subject = "Password reset"
    from_email = "no-replay@hop-hop-shop.me"

    send_mail(subject=subject, message=reset_url, from_email=from_email, recipient_list=[email])