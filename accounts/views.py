from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re
import secrets
from django.contrib.auth import login, logout, models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import LoginCode, CodeRequest
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages


ALLOWED_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com", "protonmail.com", "zoho.com", "gmx.com"}
MAX_CODES_PER_HOUR = 3
MAX_CODE_ATTEMPTS = 3

def is_allowed_email(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    domain = email.split("@")[-1]
    return domain in ALLOWED_DOMAINS



def enter_email(request):
    error = ""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        # How many codes were sent to this email in the last hour?
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent = CodeRequest.objects.filter(email=email, created_at__gte=one_hour_ago).count()

        if not is_allowed_email(email):
            error = "Please use a Gmail, Yahoo, Hotmail or Outlook address."
        elif recent >= MAX_CODES_PER_HOUR:
            messages.error(request, "Too many codes requested for this email. Please try again in an hour.")
            return redirect("/")
        else:
            # Write it in the logbook
            CodeRequest.objects.create(email=email)

            # Make a random 6-digit code, like 042917
            code = f"{secrets.randbelow(1_000_000):06d}"

            # Remove old codes for this email, then save the new one (scrambled)
            LoginCode.objects.filter(email=email).delete()
            LoginCode.objects.create(email=email, code_hash=make_password(code))

            send_mail(
                "Your login code",
                f"Your code is {code}. It expires in 10 minutes.",
                None,
                [email],
            )

            # Remember the email, and how many codes are left this hour
            request.session["login_email"] = email
            request.session["codes_left"] = MAX_CODES_PER_HOUR - (recent + 1)
            return redirect("enter_code")

    return render(request, "accounts/enter_email.html", {"error": error})


def enter_code(request):
    email = request.session.get("login_email")
    if not email:
        return redirect("enter_email")

    error = ""
    if request.method == "POST":
        typed = request.POST.get("code", "").strip()
        login_code = LoginCode.objects.filter(email=email).first()

        if login_code is None or login_code.is_expired():
            error = "This code has expired. Please ask for a new one."
        elif check_password(typed, login_code.code_hash):
            # Correct! The code can't be used again
            login_code.delete()
            user = User.objects.filter(email=email).first()
            if user is None:
                # New person: remember they're verified, then let them pick a username
                request.session["verified_email"] = email
                return redirect("choose_username")
            login(request, user)
            return redirect("/")
        else:
            login_code.attempts += 1
            if login_code.attempts >= MAX_CODE_ATTEMPTS:
                    # Too many wrong tries: throw the code away
                login_code.delete()
                del request.session["login_email"]
                if request.session.get("codes_left") == 0:
                    # No codes left this hour either: send them home
                    messages.error(request, "You've used all your codes for this email. Please try again in an hour or use another email.")
                    return redirect("/")
                messages.error(request, "Too many wrong codes. Please request a new code or use another email.")
                return redirect("enter_email")
            login_code.save()
            tries_left = MAX_CODE_ATTEMPTS - login_code.attempts
            error = f"Wrong code. You have {tries_left} {'try' if tries_left == 1 else 'tries'} left."

    codes_left = request.session.get("codes_left")
    return render(request, "accounts/enter_code.html", {"email": email, "error": error, "codes_left": codes_left})


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def choose_username(request):
    email = request.session.get("verified_email")
    if not email:
        return redirect("enter_email")

    error = ""
    username = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        if not USERNAME_PATTERN.match(username):
            error = "Use 3–20 letters, numbers or underscores (_)."
        elif User.objects.filter(username__iexact=username).exists():
            error = "Sorry, that username is taken. Try another."
        else:
            # Create the account (no password needed; we use email codes)
            user = User.objects.create_user(username=username, email=email)
            del request.session["verified_email"]
            login(request, user)
            return redirect("/")

    return render(request, "accounts/choose_username.html", {"error": error, "username": username})

def log_out(request):
    if request.method == "POST":
        logout(request)
    return redirect("/")


