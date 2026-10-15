
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import timedelta

from django.utils import timezone

from .models import Project


User = get_user_model()


class ProjectTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )

        self.project = Project.objects.create(
            name="Owner Project",
            description="Project for testing",
            owner=self.owner,
            status=Project.Status.PLANNING,
        )

    def test_project_list_shows_only_own_projects(self) -> None:
        Project.objects.create(
            name="Other Project",
            owner=self.other_user,
        )

        self.client.force_login(self.owner)
        response = self.client.get(reverse("projects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner Project")
        self.assertNotContains(response, "Other Project")

    def test_owner_can_create_project(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "New Project",
                "description": "Created in a test",
                "status": Project.Status.PLANNING,
                "deadline": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "projects:detail",
                args=[Project.objects.get(name="New Project").pk],
            ),
        )

        project = Project.objects.get(name="New Project")
        self.assertEqual(project.owner, self.owner)

    def test_owner_can_update_project(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:update", args=[self.project.pk]),
            {
                "name": "Updated Project",
                "description": "Updated description",
                "status": Project.Status.ACTIVE,
                "deadline": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("projects:detail", args=[self.project.pk]),
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated Project")
        self.assertEqual(self.project.status, Project.Status.ACTIVE)

    def test_other_user_cannot_update_project(self) -> None:
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("projects:update", args=[self.project.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete_project(self) -> None:
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("projects:delete", args=[self.project.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Project.objects.filter(pk=self.project.pk).exists()
        )

    def test_owner_can_delete_project(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("projects:delete", args=[self.project.pk])
        )

        self.assertRedirects(response, reverse("projects:list"))
        self.assertFalse(
            Project.objects.filter(pk=self.project.pk).exists()
        )
    def test_cannot_create_project_with_past_deadline(self) -> None:
        self.client.force_login(self.owner)

        past_date = (
            timezone.localdate() - timedelta(days=1)
        ).isoformat()

        response = self.client.post(
            reverse("projects:create"),
            {
                "name": "Invalid Project",
                "description": "Past deadline test",
                "status": Project.Status.PLANNING,
                "deadline": past_date,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Project.objects.filter(name="Invalid Project").exists()
        )
        self.assertContains(
            response,
            "Deadline cannot be earlier than creation date.",
        )

    def test_other_user_cannot_post_update(self) -> None:
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("projects:update", args=[self.project.pk]),
            {
                "name": "Unauthorized Change",
                "description": "Should not be saved",
                "status": Project.Status.ACTIVE,
                "deadline": "",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Owner Project")

    def test_other_user_cannot_post_delete(self) -> None:
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("projects:delete", args=[self.project.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Project.objects.filter(pk=self.project.pk).exists()
        )