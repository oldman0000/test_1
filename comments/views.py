from django.shortcuts import render, redirect
from .models import Comment


def home(request):
    # Someone pressed "Post"
    if request.method == "POST":
        # Only logged-in users may post
        if not request.user.is_authenticated:
            return redirect("/login/")

        text = request.POST.get("text", "").strip()
        if text:
            # The name comes from their account, not from a text box
            Comment.objects.create(name=request.user.username, text=text)
        return redirect("/")

    # Someone just opened the page: show all comments, newest first
    comments = Comment.objects.order_by("-created_at")
    return render(request, "comments/home.html", {"comments": comments})