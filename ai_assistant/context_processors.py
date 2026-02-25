from .models import UserProfile
from django.db.utils import OperationalError, ProgrammingError


def user_profile(request):
    if not request.user.is_authenticated:
        return {"user_profile": None}

    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {"user_profile": profile}
    except (OperationalError, ProgrammingError):
        return {"user_profile": None}
