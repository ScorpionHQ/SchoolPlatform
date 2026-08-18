

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0001_initial'),
        ('students', '0001_initial'),
        ('subjects', '0001_initial'),
        ('teachers', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='grade',
            constraint=models.UniqueConstraint(fields=('student', 'subject', 'exam_name'), name='unique_grade_per_student_subject_exam'),
        ),
    ]
