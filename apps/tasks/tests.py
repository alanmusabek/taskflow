from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Project
from apps.teams.models import Membership, Team

from .models import Task


User = get_user_model()


class TaskTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )

        self.member = User.objects.create_user(
            email="member@example.com",
            password="TestPassword123!",
        )

        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="TestPassword123!",
        )

        self.project = Project.objects.create(
            name="Test Project",
            owner=self.owner,
        )

        self.team = Team.objects.create(
            name="Development Team",
            project=self.project,
        )

        Membership.objects.create(
            team=self.team,
            user=self.member,
        )

        self.task = Task.objects.create(
            project=self.project,
            title="Initial Task",
            assigned_to=self.member,
        )

    def test_owner_can_create_task(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:create",
                args=[self.project.pk],
            ),
            {
                "title": "New Task",
                "description": "Test",
                "assigned_to": self.member.pk,
                "status": Task.Status.TODO,
                "priority": Task.Priority.HIGH,
                "due_date": "",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Task.objects.filter(title="New Task").exists()
        )

    def test_member_can_view_task(self) -> None:
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "tasks:detail",
                args=[self.task.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_view_task(self) -> None:
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse(
                "tasks:detail",
                args=[self.task.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_member_can_update_status(self) -> None:
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:update-status",
                args=[self.task.pk],
            ),
            {"status": Task.Status.DONE},
        )

        self.assertEqual(response.status_code, 200)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.status,
            Task.Status.DONE,
        )

    def test_outsider_cannot_update_status(self) -> None:
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse(
                "tasks:update-status",
                args=[self.task.pk],
            ),
            {"status": Task.Status.DONE},
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_task(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "tasks:delete",
                args=[self.task.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Task.objects.filter(pk=self.task.pk).exists()
        )

    def test_member_cannot_delete_task(self) -> None:
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "tasks:delete",
                args=[self.task.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_unrelated_user_cannot_be_assigned(self) -> None:
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Task.objects.create(
                project=self.project,
                title="Invalid Assignment",
                assigned_to=self.outsider,
            )