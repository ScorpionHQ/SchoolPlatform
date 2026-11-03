from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_encode,
)
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps, UnidentifiedImageError

from parents.models import Parent
from students.models import Student
from teachers.models import Teacher

from institutions.tenant import institutions_for_user

from .audit import log_action
from .forms import PasswordChangeForm, PasswordResetRequestForm, SetNewPasswordForm
from .models import AuditLog, User

LOGIN_MAX_ATTEMPTS = 5

LOGIN_LOCKOUT_SECONDS = 15 * 60

LOGIN_IP_MULTIPLIER = 5


def _login_max_attempts():

    return getattr(
        settings,
        "LOGIN_MAX_ATTEMPTS",
        LOGIN_MAX_ATTEMPTS,
    )


def _login_lockout_seconds():

    return getattr(
        settings,
        "LOGIN_LOCKOUT_SECONDS",
        LOGIN_LOCKOUT_SECONDS,
    )


def _client_ip(request):
    """Return the real client IP behind Render's proxy."""

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "")


def _login_cache_keys(request, login_code):

    return (
        f"login:code:{login_code.strip().lower()}",
        f"login:ip:{_client_ip(request)}",
    )


def _is_login_locked(request, login_code):
    """True when this code or IP has too many recent failures."""

    code_key, ip_key = _login_cache_keys(request, login_code)

    limit = _login_max_attempts()

    if cache.get(code_key, 0) >= limit:
        return True

    return cache.get(ip_key, 0) >= limit * LOGIN_IP_MULTIPLIER


def _register_login_failure(request, login_code):
    """Count one failed attempt, keeping the original expiry window."""

    timeout = _login_lockout_seconds()

    for key in _login_cache_keys(request, login_code):

        try:
            cache.incr(key)

        except ValueError:
            cache.set(key, 1, timeout)


def _clear_login_failures(request, login_code):

    for key in _login_cache_keys(request, login_code):
        cache.delete(key)


def _too_many_attempts_message():

    minutes = max(
        _login_lockout_seconds() // 60,
        1,
    )

    return _(
        "Too many failed login attempts. "
        "Please try again in {minutes} minutes."
    ).format(minutes=minutes)


def login_view(request):

    if request.method == "POST":

        login_code = request.POST.get(
            "login_code",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        if _is_login_locked(request, login_code):

            messages.error(
                request,
                _too_many_attempts_message(),
            )

            return render(
                request,
                "accounts/login.html",
                status=429,
            )

        try:

            user = User.objects.get(
                login_code=login_code,
            )

        except User.DoesNotExist:

            _register_login_failure(request, login_code)

            messages.error(
                request,
                _("Invalid login code or password."),
            )

            return render(
                request,
                "accounts/login.html",
            )

        authenticated_user = authenticate(
            request,
            username=user.username,
            password=password,
        )

        if authenticated_user is None:

            _register_login_failure(request, login_code)

            messages.error(
                request,
                _("Invalid login code or password."),
            )

            return render(
                request,
                "accounts/login.html",
            )

        _clear_login_failures(request, login_code)

        login(
            request,
            authenticated_user,
        )

        log_action(
            request,
            AuditLog.Action.LOGIN,
            user=authenticated_user,
            description=str(_("Signed in")),
        )

        if authenticated_user.must_change_password:

            messages.warning(
                request,
                _("You must change your password before continuing."),
            )

            return redirect("change_password")

        if authenticated_user.role == User.Role.SYSTEM_ADMIN:
            return redirect("dashboard")

        if authenticated_user.role in [
            User.Role.MANAGER,
            User.Role.ASSISTANT_MANAGER,
        ]:

            institution_count = institutions_for_user(
                authenticated_user,
            ).count()

            if institution_count > 1:
                return redirect("institutions:select")

            if institution_count == 0:

                messages.warning(
                    request,
                    _(
                        "No institution is assigned to your account yet. "
                        "Please contact the system administrator."
                    ),
                )

            return redirect("dashboard")

        elif authenticated_user.role == User.Role.TEACHER:
            return redirect("teachers:dashboard")

        elif authenticated_user.role == User.Role.STUDENT:
            return redirect("student_dashboard")

        elif authenticated_user.role == User.Role.PARENT:
            return redirect("parent_dashboard")

        return redirect("dashboard")

    return render(
        request,
        "accounts/login.html",
    )


@login_required
def profile_view(request):

    profile = None

    if request.user.role == User.Role.STUDENT:

        profile = Student.objects.select_related(
            "classroom",
            "institution",
        ).filter(
            user=request.user,
        ).first()

    elif request.user.role == User.Role.PARENT:

        profile = Parent.objects.filter(
            user=request.user,
        ).first()

    elif request.user.role == User.Role.TEACHER:

        profile = Teacher.objects.select_related(
            "institution",
        ).filter(
            user=request.user,
        ).first()

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def change_password_view(request):

    form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None,
    )

    if request.method == "POST":

        if form.is_valid():

            request.user.set_password(
                form.cleaned_data["new_password"],
            )

            request.user.must_change_password = False

            request.user.save()

            log_action(
                request,
                AuditLog.Action.PASSWORD,
                obj=request.user,
                description=str(_("Changed password")),
            )

            login(
                request,
                request.user,
            )

            messages.success(
                request,
                _("Your password has been changed successfully."),
            )

            return redirect("dashboard")

    return render(
        request,
        "accounts/change_password.html",
        {
            "form": form,
        },
    )


@login_required
@require_POST
def logout_view(request):

    log_action(
        request,
        AuditLog.Action.LOGOUT,
        description=str(_("Signed out")),
    )

    logout(request)

    return redirect("login")


def password_reset_request(request):
    """Send a reset link to the email registered for a login code.

    The same success message is shown whether or not the account exists, so
    the page cannot be used to discover valid login codes.
    """

    form = PasswordResetRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        login_code = form.cleaned_data["login_code"]

        user = User.objects.filter(
            login_code=login_code,
            is_active=True,
        ).first()

        if user and user.email:

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            token = default_token_generator.make_token(user)

            reset_url = request.build_absolute_uri(
                reverse(
                    "password_reset_confirm",
                    kwargs={
                        "uidb64": uidb64,
                        "token": token,
                    },
                )
            )

            send_mail(
                subject=str(_("Reset your password")),
                message=str(
                    _(
                        "Hello {name}, use this link to set a new password: "
                        "{link} If you did not request this, ignore this email."
                    )
                ).format(
                    name=user.get_full_name() or user.username,
                    link=reset_url,
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        messages.success(
            request,
            _(
                "If the account has an email address on file, "
                "a reset link has been sent. Please check the inbox."
            ),
        )

        return redirect("login")

    return render(
        request,
        "accounts/password_reset.html",
        {
            "form": form,
        },
    )


class SetNewPasswordView(PasswordResetConfirmView):
    """The link from the reset email opens this view."""

    template_name = "accounts/password_reset_confirm.html"

    form_class = SetNewPasswordForm

    success_url = reverse_lazy("login")

    def form_valid(self, form):

        response = super().form_valid(form)

        log_action(
            self.request,
            AuditLog.Action.PASSWORD,
            obj=form.user,
            user=form.user,
            description=str(_("Reset password")),
        )

        messages.success(
            self.request,
            _("Your password has been reset. Please log in."),
        )

        return response


@login_required
def upload_profile_photo(request):

    next_url = _safe_next_url(request)

    if request.method == "POST":

        if request.POST.get("skip"):
            return redirect(_photo_redirect_target(request, next_url))

        image = request.FILES.get("profile_image")

        if not image:

            messages.error(
                request,
                _("Please choose an image first."),
            )

        else:

            try:
                cleaned_image = _prepare_profile_photo(
                    image,
                    request.user,
                )

            except ValidationError as error:

                messages.error(
                    request,
                    error.messages[0],
                )

            else:

                request.user.profile_image = cleaned_image

                request.user.save(update_fields=["profile_image"])

                messages.success(
                    request,
                    _("Profile photo uploaded successfully."),
                )

                return redirect(
                    _photo_redirect_target(request, next_url),
                )

    return render(
        request,
        "accounts/upload_photo.html",
        {
            "next": next_url,
        },
    )


PHOTO_MAX_BYTES = 5 * 1024 * 1024

PHOTO_MAX_DIMENSION = 800

PHOTO_ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP")

PHOTO_DECODE_ERRORS = (
    UnidentifiedImageError,
    OSError,
    SyntaxError,
    ValueError,
    Image.DecompressionBombError,
)


def _prepare_profile_photo(uploaded_image, user):
    """Validate, rotate, shrink and re-encode an uploaded profile photo."""

    if uploaded_image.size > PHOTO_MAX_BYTES:
        raise ValidationError(_("Image must be less than 5 MB."))

    try:

        probe = Image.open(uploaded_image)
        probe.verify()

    except PHOTO_DECODE_ERRORS:
        raise ValidationError(_("The uploaded file is not a valid image."))

    uploaded_image.seek(0)

    try:

        image = Image.open(uploaded_image)

        if image.format not in PHOTO_ALLOWED_FORMATS:
            raise ValidationError(
                _("Only JPEG, PNG or WebP images are allowed."),
            )

        image = ImageOps.exif_transpose(image)

        if image.mode in ("RGBA", "LA", "P"):

            image = image.convert("RGBA")

            background = Image.new(
                "RGB",
                image.size,
                (255, 255, 255),
            )

            background.paste(
                image,
                mask=image.split()[-1],
            )

            image = background

        elif image.mode != "RGB":

            image = image.convert("RGB")

        image.thumbnail(
            (PHOTO_MAX_DIMENSION, PHOTO_MAX_DIMENSION),
            Image.Resampling.LANCZOS,
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=85,
            optimize=True,
        )

    except ValidationError:
        raise

    except PHOTO_DECODE_ERRORS:
        raise ValidationError(_("The uploaded file is not a valid image."))

    return ContentFile(
        buffer.getvalue(),
        name=f"profile-{user.pk}.jpg",
    )


def _safe_next_url(request):
    """Return the ``next`` target only when it points to this host."""

    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or ""
    ).strip()

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url

    return ""


def _photo_redirect_target(request, next_url):

    if next_url:
        return next_url

    if request.user.role == User.Role.TEACHER:
        return "teachers:dashboard"

    if request.user.role == User.Role.PARENT:
        return "parent_dashboard"

    if request.user.role == User.Role.STUDENT:
        return "student_dashboard"

    return "dashboard"
