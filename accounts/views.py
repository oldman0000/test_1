import re
import secrets
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import LoginCode


def enter_email(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if email:
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

            # Remember which email is logging in, for the next page
            request.session["login_email"] = email
            return redirect("enter_code")

    return render(request, "accounts/enter_email.html")


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
        elif login_code.attempts >= 5:
            error = "Too many wrong tries. Please ask for a new code."
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
            login_code.save()
            error = "Wrong code. Try again."

    return render(request, "accounts/enter_code.html", {"email": email, "error": error})


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