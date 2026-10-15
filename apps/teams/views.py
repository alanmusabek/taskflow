
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import MembershipForm, TeamForm
from .models import Membership, Team

User = get_user_model()


def can_manage_team(user, team):
    return user.is_superuser or team.project.owner_id == user.id


@login_required
def team_list(request):
    teams = Team.objects.filter(
        project__owner=request.user
    ).select_related("project").prefetch_related("membership_set")

    if request.user.is_superuser:
        teams = Team.objects.select_related(
            "project"
        ).prefetch_related("membership_set")

    return render(request, "teams/team_list.html", {"teams": teams})


@login_required
def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST, user=request.user)
        if form.is_valid():
            team = form.save()
            messages.success(request, "Team created successfully.")
            return redirect("teams:team_detail", team_id=team.pk)
    else:
        form = TeamForm(user=request.user)

    return render(request, "teams/team_form.html", {"form": form})


@login_required
def team_detail(request, team_id):
    team = get_object_or_404(
        Team.objects.select_related("project"),
        pk=team_id,
    )

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    members = Membership.objects.filter(
        team=team
    ).select_related("user")

    form = MembershipForm(team=team)

    return render(
        request,
        "teams/team_detail.html",
        {"team": team, "members": members, "form": form},
    )


@login_required
def team_update(request, team_id):
    team = get_object_or_404(Team, pk=team_id)

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    if request.method == "POST":
        form = TeamForm(
            request.POST, instance=team, user=request.user
        )
        if form.is_valid():
            updated_team = form.save()
            messages.success(request, "Team updated successfully.")
            return redirect(
                "teams:team_detail", team_id=updated_team.pk
            )
    else:
        form = TeamForm(instance=team, user=request.user)

    return render(
        request,
        "teams/team_form.html",
        {"form": form, "team": team},
    )


@login_required
@require_POST
def team_delete(request, team_id):
    team = get_object_or_404(Team, pk=team_id)

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    team.delete()
    messages.success(request, "Team deleted successfully.")
    return redirect("teams:team_list")


@login_required
@require_POST
def member_add(request, team_id):
    team = get_object_or_404(Team, pk=team_id)

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    form = MembershipForm(request.POST, team=team)

    if form.is_valid():
        membership = form.save(commit=False)
        membership.team = team
        try:
            membership.save()
            messages.success(request, "Member added successfully.")
        except IntegrityError:
            messages.error(request, "This user is already a member.")
    else:
        for error in form.errors.values():
            messages.error(request, " ".join(error))

    return redirect("teams:team_detail", team_id=team.pk)


@login_required
@require_POST
def member_remove(request, team_id, membership_id):
    team = get_object_or_404(Team, pk=team_id)

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    membership = get_object_or_404(
        Membership, pk=membership_id, team=team
    )
    membership.delete()
    messages.success(request, "Member removed successfully.")

    return redirect("teams:team_detail", team_id=team.pk)


@login_required
@require_POST
def member_update_role(request, team_id, membership_id):
    team = get_object_or_404(Team, pk=team_id)

    if not can_manage_team(request.user, team):
        raise PermissionDenied

    membership = get_object_or_404(
        Membership, pk=membership_id, team=team
    )

    role = request.POST.get("role")
    valid_roles = dict(Membership.ROLE_CHOICES)

    if role in valid_roles:
        membership.role = role
        membership.save(update_fields=["role"])
        messages.success(request, "Member role updated.")
    else:
        messages.error(request, "Invalid role.")

    return redirect("teams:team_detail", team_id=team.pk)
