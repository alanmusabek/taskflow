from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.projects.models import Project

from apps.teams.models import Membership, Team


class MembershipTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email="test@example.com", password="12345678"
        )
        self.project = Project.objects.create(name="Test project")
        self.team = Team.objects.create(name="Team A", project=self.project)

    def test_duplicate_membership_is_forbidden(self) -> None:
        Membership.objects.create(team=self.team, user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membership.objects.create(team=self.team, user=self.user)

    def test_duplicate_team_name_in_project_is_forbidden(self) -> None:
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Team.objects.create(name="Team A", project=self.project)