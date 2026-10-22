from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.projects.models import Project
from apps.teams.models import Membership, Team

from .models import Task, TaskStatus

User = get_user_model()


def make_user(email, **extra):
    return User.objects.create_user(
        email=email, password="pass12345", first_name="F", last_name="L", **extra
    )


class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = make_user("owner@x.com")
        cls.member = make_user("member@x.com")
        cls.outsider = make_user("outsider@x.com")
        cls.project = Project.objects.create(name="P", owner=cls.owner)
        cls.team = Team.objects.create(name="T", project=cls.project)
        cls.membership = Membership.objects.create(team=cls.team, user=cls.member)
        cls.task = Task.objects.create(
            title="Task", project=cls.project, created_by=cls.owner, assignee=cls.member
        )


class TaskModelTests(BaseCase):
    def test_assignee_must_be_participant(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(
                title="x", project=self.project, created_by=self.owner,
                assignee=self.outsider,
            )

    def test_creator_must_be_participant(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(title="x", project=self.project, created_by=self.outsider)

    def test_due_date_in_past_rejected_on_create(self):
        with self.assertRaises(ValidationError):
            Task.objects.create(
                title="x", project=self.project, created_by=self.owner,
                due_date=timezone.localdate() - timedelta(days=1),
            )

    def test_overdue_task_can_still_be_completed(self):
        task = Task.objects.create(
            title="x", project=self.project, created_by=self.owner,
            due_date=timezone.localdate(),
        )
        Task.objects.filter(pk=task.pk).update(
            due_date=timezone.localdate() - timedelta(days=3)
        )
        task = Task.objects.get(pk=task.pk)
        task.status = TaskStatus.DONE
        task.save()
        self.assertEqual(Task.objects.get(pk=task.pk).status, TaskStatus.DONE)

    def test_task_with_removed_assignee_stays_editable(self):
        self.membership.delete()
        task = Task.objects.get(pk=self.task.pk)
        task.status = TaskStatus.IN_PROGRESS
        task.save()

    def test_new_assignee_still_validated_on_update(self):
        task = Task.objects.get(pk=self.task.pk)
        task.assignee = self.outsider
        with self.assertRaises(ValidationError):
            task.save()


class TaskViewTests(BaseCase):
    def test_login_required(self):
        r = self.client.get(reverse("tasks:detail", args=[self.task.pk]))
        self.assertEqual(r.status_code, 302)

    def test_outsider_forbidden(self):
        self.client.force_login(self.outsider)
        for name, args in [
            ("tasks:list", [self.project.pk]),
            ("tasks:create", [self.project.pk]),
            ("tasks:detail", [self.task.pk]),
            ("tasks:update", [self.task.pk]),
            ("tasks:delete", [self.task.pk]),
        ]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403, name)

    def test_pages_render(self):
        self.client.force_login(self.owner)
        for name, args in [
            ("tasks:mine", []),
            ("tasks:list", [self.project.pk]),
            ("tasks:create", [self.project.pk]),
            ("tasks:detail", [self.task.pk]),
            ("tasks:update", [self.task.pk]),
            ("tasks:delete", [self.task.pk]),
        ]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_create_task(self):
        self.client.force_login(self.member)
        r = self.client.post(
            reverse("tasks:create", args=[self.project.pk]),
            {"title": "New", "status": "to_do", "priority": "low"},
        )
        task = Task.objects.get(title="New")
        self.assertRedirects(r, reverse("tasks:detail", args=[task.pk]))
        self.assertEqual(task.created_by, self.member)

    def test_create_with_past_due_date_shows_form_error(self):
        self.client.force_login(self.owner)
        r = self.client.post(
            reverse("tasks:create", args=[self.project.pk]),
            {"title": "New", "status": "to_do", "priority": "low",
             "due_date": (timezone.localdate() - timedelta(days=1)).isoformat()},
        )
        self.assertEqual(r.status_code, 200)
        self.assertFormError(r.context["form"], "due_date", "Due date cannot be earlier than creation date.")

    def test_superuser_can_create_in_any_project(self):
        admin = make_user("admin@x.com", is_superuser=True, is_staff=True)
        self.client.force_login(admin)
        r = self.client.post(
            reverse("tasks:create", args=[self.project.pk]),
            {"title": "By admin", "status": "to_do", "priority": "low"},
        )
        self.assertEqual(r.status_code, 302)

    def test_member_who_is_not_creator_or_assignee_cannot_edit(self):
        other = make_user("other@x.com")
        Membership.objects.create(team=self.team, user=other)
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("tasks:update", args=[self.task.pk])).status_code, 403)

    def test_delete(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("tasks:delete", args=[self.task.pk]))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_filters(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse("tasks:list", args=[self.project.pk]), {"status": "done"})
        self.assertEqual(len(r.context["tasks"]), 0)
        r = self.client.get(reverse("tasks:list", args=[self.project.pk]), {"q": "task"})
        self.assertEqual(len(r.context["tasks"]), 1)

    def test_my_tasks(self):
        self.client.force_login(self.member)
        r = self.client.get(reverse("tasks:mine"))
        self.assertEqual(list(r.context["tasks"]), [self.task])
