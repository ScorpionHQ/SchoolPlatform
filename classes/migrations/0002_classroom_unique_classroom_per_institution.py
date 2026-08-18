

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0001_initial'),
        ('institutions', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='classroom',
            constraint=models.UniqueConstraint(fields=('institution', 'name', 'level', 'academic_year'), name='unique_classroom_per_institution'),
        ),
    ]
