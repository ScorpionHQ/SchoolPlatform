

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(max_length=50)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='institutions/logos/')),
                ('address', models.TextField(blank=True)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('users', models.ManyToManyField(blank=True, related_name='institutions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Institution',
                'verbose_name_plural': 'Institutions',
                'ordering': ['name'],
            },
        ),
    ]
