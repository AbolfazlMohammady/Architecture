from functools import wraps
from django.core.exceptions import PermissionDenied

def role_required(roles):
    """
    دکوریتور برای کنترل دسترسی بر اساس نقش (Role)
    roles: لیست نام نقش‌های مجاز (str)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied
            user_roles = set(user.roles.values_list('name', flat=True))
            if not user_roles.intersection(set(roles)):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 