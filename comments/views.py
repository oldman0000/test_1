from django.shortcuts import render, redirect
from .models import Comment

def home(request):
    # Someone pressed "Post": save their comment
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        text = request.POST.get("text", "").strip()
        if name and text:
            Comment.objects.create(name=name, text=text)
        return redirect("/")

    # Someone just opened the page: show all comments, newest first
    comments = Comment.objects.order_by("-created_at")
    return render(request, "comments/home.html", {"comments": comments})