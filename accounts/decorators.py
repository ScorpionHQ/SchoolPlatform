from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(*roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.role not in roles:

                raise PermissionDenied

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


teacher_required = role_required(
    User.Role.TEACHER,
)

student_required = role_required(
    User.Role.STUDENT,
)

parent_required = role_required(
    User.Role.PARENT,
)

manager_required = role_required(
    User.Role.MANAGER,
    User.Role.SYSTEM_ADMIN,
    User.Role.ASSISTANT_MANAGER,
)