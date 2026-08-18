from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("assistant", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="sources",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=_(
                    "Sources cited by the assistant, as a list of "
                    "{title, url} objects."
                ),
            ),
        ),
    ]
