from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
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
            Comment.objects.create(name=request.user.username, text=text, author=request.user)
        return redirect("/")

    # Someone just opened the page: show all comments, newest first
    comments = Comment.objects.order_by("-created_at")
    return render(request, "comments/home.html", {"comments": comments})



def delete_comment(request, comment_id):
    # Only allow deleting with a form (POST), not by just visiting a link
    if request.method != "POST":
        return redirect("/")

    # Find the comment, or show "404 Not Found" if it doesn't exist
    comment = get_object_or_404(Comment, id=comment_id)

    # The permission check: is this person the author?
    if comment.author != request.user:
        return HttpResponseForbidden("You can only delete your own comments.")

    comment.delete()
    return redirect("/")