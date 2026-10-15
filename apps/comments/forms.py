from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Write a comment..."}
            ),
        }
        labels = {"content": ""}

    def clean_content(self):
        content = self.cleaned_data["content"].strip()

        if not content:
            raise forms.ValidationError("Comment cannot be empty.")

        return content
