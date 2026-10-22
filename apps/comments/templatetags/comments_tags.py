from django import template

from apps.comments.access import can_access_task, can_modify_comment
from apps.comments.forms import CommentForm

register = template.Library()


@register.inclusion_tag("comments/_task_comments.html", takes_context=True)
def task_comments(context, task):
    """Comment list and add-form to embed into the task detail page.

    Usage in a template:
        {% load comments_tags %}
        {% task_comments task %}
    """
    user = context["request"].user

    if not can_access_task(user, task):
        return {"allowed": False}

    comments = []
    for comment in task.comments.select_related("author"):
        comment.user_can_modify = can_modify_comment(user, comment)
        comments.append(comment)

    return {
        "allowed": True,
        "task": task,
        "comments": comments,
        "form": CommentForm(),
    }
