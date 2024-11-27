import os

from django.core.mail import send_mail

from utils.mail_sender import EmailUtil


def send_reset_password_email(token, email):
    reset_url = f"{os.environ['BASE_URL']}{os.environ['PASSWORD_RESET_PATH']}?key={token}&user_email={email}"

    subject = "Password reset"
    from_email = "no-replay@hop-hop-shop.me"

    send_mail(subject=subject, message=reset_url, from_email=from_email, recipient_list=[email])


def send_email_verification_url(user, token):
    base_url = os.getenv("BASE_URL")
    abs_url = base_url + "/?token=" + str(token)
    email_body = 'Hi ' + user.first_name + ',' + \
                 '\nThank you for signing up! Please click the button below to ' + \
                 'verify your email address and complete your registration: \n' + abs_url

    data = {'email_body': email_body, 'to_email': user.email,
            'email_subject': 'Verify your email'}

    EmailUtil.send_email(data=data)
