from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.teams.models import Membership, Team

from .models import Comment

User = get_user_model()


def make_user(email):
    return User.objects.create_user(
        email=email,
        password="pass12345",
        first_name="Test",
        last_name="User",
    )


class CommentTestBase(TestCase):
    """Project with an owner, two members and one outsider."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner@test.com")
        cls.author = make_user("author@test.com")
        cls.member = make_user("member@test.com")
        cls.outsider = make_user("outsider@test.com")

        cls.project = Project.objects.create(name="Project", owner=cls.owner)
        cls.team = Team.objects.create(name="Team", project=cls.project)

        Membership.objects.create(team=cls.team, user=cls.author)
        Membership.objects.create(team=cls.team, user=cls.member)

        cls.task = Task.objects.create(
            project=cls.project,
            title="Task",
            created_by=cls.owner,
        )

        cls.comment = Comment.objects.create(
            task=cls.task,
            author=cls.author,
            content="Hello",
        )


class CommentModelTests(CommentTestBase):
    def test_timestamps_are_set(self):
        self.assertIsNotNone(self.comment.created_at)
        self.assertIsNotNone(self.comment.updated_at)

    def test_empty_content_is_rejected(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Comment.objects.create(
                task=self.task, author=self.author, content="   "
            )

    def test_deleting_task_deletes_comments(self):
        self.task.delete()
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_author_with_comments_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.author.delete()


class CommentAccessTests(CommentTestBase):
    def test_member_can_view_list(self):
        self.client.force_login(self.member)
        response = self.client.get(
            reverse("comments:list", args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_view_list(self):
        self.client.force_login(self.outsider)
        response = self.client.get(
            reverse("comments:list", args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(
            reverse("comments:list", args=[self.task.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_member_can_create_comment(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("comments:create", args=[self.task.pk]),
            {"content": "New comment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(
                task=self.task, author=self.member, content="New comment"
            ).exists()
        )

    def test_outsider_cannot_create_comment(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("comments:create", args=[self.task.pk]),
            {"content": "Hack"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 1)

    def test_empty_comment_is_not_created(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("comments:create", args=[self.task.pk]),
            {"content": "   "},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)


class CommentModifyTests(CommentTestBase):
    def test_author_can_edit(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("comments:update", args=[self.comment.pk]),
            {"content": "Edited"},
        )
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Edited")

    def test_other_member_cannot_edit(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("comments:update", args=[self.comment.pk]),
            {"content": "Edited"},
        )
        self.assertEqual(response.status_code, 403)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Hello")

    def test_project_owner_can_edit(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("comments:update", args=[self.comment.pk]),
            {"content": "Moderated"},
        )
        self.assertEqual(response.status_code, 302)

    def test_author_can_delete(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("comments:delete", args=[self.comment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_other_member_cannot_delete(self):
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("comments:delete", args=[self.comment.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_project_owner_can_delete(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("comments:delete", args=[self.comment.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
