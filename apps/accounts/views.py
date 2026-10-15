from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import RegistrationForm, ProfileUpdateForm

@require_POST
def register(request: HttpRequest) -> JsonResponse:
    form = RegistrationForm(request.POST)

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    user = form.save()

    return JsonResponse(
        {
            "id": user.pk,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        status=201,
    )

@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    email = request.POST.get("email", "")
    password = request.POST.get("password", "")

    user = authenticate(
        request,
        username=email,
        password=password,
    )

    if user is None:
        return JsonResponse(
            {"error": "Invalid email or password."},
            status=401,
        )

    login(request, user)

    return JsonResponse({
        "message": "Login successful.",
        "user_id": user.pk,
        "email": user.email,
    })


@require_POST
@login_required
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)

    return JsonResponse({
        "message": "Logout successful.",
    })


@require_GET
@login_required
def profile_view(request: HttpRequest) -> JsonResponse:
    user = request.user

    return JsonResponse({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    })

@require_http_methods(["POST"])
@login_required
def update_profile_view(request: HttpRequest) -> JsonResponse:
    form = ProfileUpdateForm(
        request.POST,
        instance=request.user,
    )

    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    user = form.save()

    return JsonResponse({
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    })