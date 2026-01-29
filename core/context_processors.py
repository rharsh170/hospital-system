from .models import UserProfile


def user_role(request):
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.userprofile.role
        except UserProfile.DoesNotExist:
            role = None
    return {'current_role': role}

