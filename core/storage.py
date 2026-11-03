import mimetypes
from io import BytesIO
from urllib.parse import quote

from django.core.files.base import File
from django.core.files.storage import Storage
from django.db import transaction
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Store uploaded files in the database.

    Free hosts give the app an ephemeral disk, so a profile photo saved to
    ``MEDIA_ROOT`` disappears on the next restart. When no S3-compatible
    bucket is configured, keeping small files in the database is the
    simplest way to make them survive a redeploy.
    """

    def _open(self, name, mode="rb"):

        from .models import StoredFile

        stored = StoredFile.objects.get(name=name)

        return File(
            BytesIO(memoryview(stored.content).tobytes()),
            name=name,
        )

    def _save(self, name, content):

        from .models import StoredFile

        content.seek(0)

        data = content.read()

        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )

        with transaction.atomic():

            StoredFile.objects.update_or_create(
                name=name,
                defaults={
                    "content": data,
                    "content_type": content_type,
                    "size": len(data),
                },
            )

        return name

    def delete(self, name):

        from .models import StoredFile

        StoredFile.objects.filter(name=name).delete()

    def exists(self, name):

        from .models import StoredFile

        return StoredFile.objects.filter(name=name).exists()

    def size(self, name):

        from .models import StoredFile

        return StoredFile.objects.get(name=name).size

    def url(self, name):

        from django.conf import settings

        return f"{settings.MEDIA_URL}{quote(name)}"


def media_content_type(name):
    """Content type for a stored file, falling back to the file extension."""

    from .models import StoredFile

    stored = StoredFile.objects.filter(name=name).first()

    if stored and stored.content_type:
        return stored.content_type

    return mimetypes.guess_type(name)[0] or "application/octet-stream"
