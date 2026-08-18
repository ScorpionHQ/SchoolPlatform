

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('institutions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stage', models.CharField(choices=[('primary', 'Primary School'), ('middle', 'Middle School'), ('preparatory', 'Preparatory School')], default='primary', max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('level', models.CharField(max_length=50)),
                ('academic_year', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classrooms', to='institutions.institution')),
            ],
            options={
                'verbose_name': 'Class Room',
                'verbose_name_plural': 'Class Rooms',
                'ordering': ['stage', 'level', 'name'],
            },
        ),
    ]
