from accounts.models import User

from .models import Institution

SESSION_KEY = "institution_id"

MANAGER_ROLES = (
    User.Role.MANAGER,
    User.Role.ASSISTANT_MANAGER,
)

PROFILE_ROLES = (
    User.Role.STUDENT,
    User.Role.TEACHER,
    User.Role.PARENT,
)


def institutions_for_user(user):
    """Institutions the given user is allowed to manage or act within."""

    if not user or not user.is_authenticated:
        return Institution.objects.none()

    if user.role == User.Role.SYSTEM_ADMIN:
        return Institution.objects.filter(is_active=True)

    if user.role in MANAGER_ROLES:
        return user.institutions.filter(is_active=True)

    return Institution.objects.none()


def profile_institution(user):
    """The single institution a non-manager user belongs to."""

    if user.role == User.Role.STUDENT:
        profile = getattr(user, "student_profile", None)
        return profile.institution if profile else None

    if user.role == User.Role.TEACHER:
        profile = getattr(user, "teacher_profile", None)
        return profile.institution if profile else None

    if user.role == User.Role.PARENT:
        profile = getattr(user, "parent_profile", None)
        if profile:
            first = profile.students.first()
            return first.institution if first else None
        return None

    return None


def _remember(session, institution_id):
    if session.get(SESSION_KEY) != institution_id:
        session[SESSION_KEY] = institution_id


def resolve_institution(user, session):
    """Return (available_institutions, current_institution) for a request."""

    if not user or not user.is_authenticated:
        return Institution.objects.none(), None

    if user.role in PROFILE_ROLES:
        institution = profile_institution(user)
        if institution:
            _remember(session, institution.pk)
            return Institution.objects.filter(pk=institution.pk), institution
        return Institution.objects.none(), None

    available = institutions_for_user(user)

    session_id = session.get(SESSION_KEY)

    institution = None

    if session_id:
        institution = available.filter(pk=session_id).first()

    if institution is None:
        institution = available.first()

    if institution:
        _remember(session, institution.pk)

    return available, institution
