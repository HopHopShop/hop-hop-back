import os

from django.core.mail import send_mail


def send_webhook_email(message):
    subject = "Coinbase Data"
    from_email = "no-replay@hop-hop-shop.me"
    to_email = os.environ['COIN_BASE_EMAIL']

    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=[to_email])