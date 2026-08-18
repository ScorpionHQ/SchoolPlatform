from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("institutions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="institution",
            name="manager_code",
            field=models.CharField(
                blank=True,
                help_text=(
                    "A dedicated login code for this school's manager. "
                    "Auto-generated if left empty."
                ),
                max_length=30,
                unique=True,
            ),
        ),
    ]
