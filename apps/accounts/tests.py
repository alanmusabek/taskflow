
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import User


class UserModelTests(TestCase):
    def test_custom_user_model_is_configured(self) -> None:
        self.assertIs(get_user_model(), User)
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertIsNone(User.username)

    def test_create_user(self) -> None:
        user = User.objects.create_user(
            email="user@example.com",
            password="SecurePassword123!",
            first_name="John",
            last_name="Smith",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Smith")
        self.assertTrue(user.check_password("SecurePassword123!"))
        self.assertNotEqual(user.password, "SecurePassword123!")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_is_normalized(self) -> None:
        user = User.objects.create_user(
            email="USER@EXAMPLE.COM",
            password="SecurePassword123!",
        )

        self.assertEqual(user.email, "USER@example.com")

    def test_email_is_required(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="SecurePassword123!",
            )

    def test_duplicate_email_is_rejected(self) -> None:
        User.objects.create_user(
            email="duplicate@example.com",
            password="SecurePassword123!",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    email="duplicate@example.com",
                    password="AnotherPassword123!",
                )

    def test_create_superuser(self) -> None:
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="SecurePassword123!",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_superuser_requires_staff_permission(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="SecurePassword123!",
                is_staff=False,
            )

    def test_superuser_requires_superuser_permission(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="SecurePassword123!",
                is_superuser=False,
            )

    def test_user_string_representation(self) -> None:
        user = User.objects.create_user(
            email="user@example.com",
            password="SecurePassword123!",
        )

        self.assertEqual(str(user), "user@example.com")


class RegistrationTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse("register")

        self.valid_data = {
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Smith",
            "password1": "SecurePassword123!",
            "password2": "SecurePassword123!",
        }

    def test_successful_registration(self) -> None:
        response = self.client.post(
            self.url,
            self.valid_data,
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["email"], "newuser@example.com")
        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["last_name"], "Smith")
        self.assertIn("id", data)
        self.assertNotIn("password", data)

        user = User.objects.get(
            email="newuser@example.com",
        )

        self.assertTrue(
            user.check_password("SecurePassword123!")
        )

    def test_registration_with_duplicate_email(self) -> None:
        User.objects.create_user(
            email="newuser@example.com",
            password="SecurePassword123!",
        )

        response = self.client.post(
            self.url,
            self.valid_data,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])
        self.assertEqual(User.objects.count(), 1)

    def test_registration_with_mismatched_passwords(self) -> None:
        data = self.valid_data.copy()
        data["password2"] = "DifferentPassword123!"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertEqual(User.objects.count(), 0)

    def test_registration_with_missing_email(self) -> None:
        data = self.valid_data.copy()
        data["email"] = ""

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["errors"])

    def test_registration_rejects_weak_password(self) -> None:
        data = self.valid_data.copy()
        data["password1"] = "123"
        data["password2"] = "123"

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertFalse(
            User.objects.filter(
                email="newuser@example.com"
            ).exists()
        )

    def test_registration_requires_post(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)


class AuthenticationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@example.com",
            password="SecurePassword123!",
            first_name="John",
            last_name="Smith",
        )

        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.profile_url = reverse("profile")

    def test_successful_login(self) -> None:
        response = self.client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "SecurePassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["user_id"],
            self.user.pk,
        )

        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(self.user.pk),
        )

    def test_login_with_wrong_password(self) -> None:
        response = self.client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())
        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_login_with_unknown_email(self) -> None:
        response = self.client.post(
            self.login_url,
            {
                "email": "unknown@example.com",
                "password": "SecurePassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_login(self) -> None:
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.login_url,
            {
                "email": "user@example.com",
                "password": "SecurePassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)

    def test_successful_logout(self) -> None:
        self.client.force_login(self.user)

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Logout successful.",
        )
        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_logout_requires_post(self) -> None:
        self.client.force_login(self.user)

        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, 405)
        self.assertIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_profile_requires_authentication(self) -> None:
        response = self.client.get(self.profile_url)

        # Current login_required behavior redirects anonymous users.
        self.assertEqual(response.status_code, 302)

    def test_login_requires_post(self) -> None:
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 405)


class ProfileTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@example.com",
            password="SecurePassword123!",
            first_name="John",
            last_name="Smith",
        )

        self.profile_url = reverse("profile")
        self.update_url = reverse("profile-update")

        self.client.force_login(self.user)

    def test_get_profile(self) -> None:
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["id"], self.user.pk)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["first_name"], "John")
        self.assertEqual(data["last_name"], "Smith")
        self.assertNotIn("password", data)

    def test_update_profile(self) -> None:
        response = self.client.post(
            self.update_url,
            {
                "first_name": "Michael",
                "last_name": "Johnson",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Michael")
        self.assertEqual(self.user.last_name, "Johnson")

    def test_profile_update_cannot_change_email(self) -> None:
        response = self.client.post(
            self.update_url,
            {
                "first_name": "Michael",
                "last_name": "Johnson",
                "email": "hacker@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            "user@example.com",
        )

    def test_profile_update_cannot_change_password(self) -> None:
        response = self.client.post(
            self.update_url,
            {
                "first_name": "Michael",
                "last_name": "Johnson",
                "password": "ChangedPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("SecurePassword123!")
        )

    def test_profile_update_requires_post(self) -> None:
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 405)

    def test_profile_update_requires_authentication(self) -> None:
        self.client.logout()

        response = self.client.post(
            self.update_url,
            {
                "first_name": "Unauthorized",
                "last_name": "User",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")

    def test_invalid_profile_update(self) -> None:
        response = self.client.post(
            self.update_url,
            {
                "first_name": "A" * 151,
                "last_name": "Smith",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "first_name",
            response.json()["errors"],
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")


class UserAdminTests(TestCase):
    def test_user_model_registered_in_admin(self) -> None:
        self.assertIn(User, admin.site._registry)

    def test_admin_searches_by_email(self) -> None:
        user_admin = admin.site._registry[User]

        self.assertIn("email", user_admin.search_fields)

    def test_admin_displays_email(self) -> None:
        user_admin = admin.site._registry[User]

        self.assertIn("email", user_admin.list_display)
