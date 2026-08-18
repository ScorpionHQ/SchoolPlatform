from django.db import migrations


def backfill_student_gender(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Student = apps.get_model("students", "Student")

    for student in Student.objects.select_related("user").all():
        user = student.user
        if user.gender != student.gender:
            user.gender = student.gender
            user.save(update_fields=["gender"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_gender"),
        ("students", "0002_student_gender"),
    ]

    operations = [
        migrations.RunPython(backfill_student_gender, noop),
    ]
