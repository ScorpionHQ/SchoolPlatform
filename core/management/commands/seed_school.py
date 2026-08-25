# -*- coding: utf-8 -*-
from datetime import date, timedelta

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed database with a school, teacher, 2 students, parent, subjects, attendance, and grades"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("This will delete ALL existing data. Are you sure? (yes/no): "))
        confirm = input().strip().lower()
        if confirm != "yes":
            self.stdout.write(self.style.ERROR("Aborted."))
            return

        from accounts.models import User
        from attendance.models import Attendance
        from classes.models import ClassRoom
        from grades.models import Grade
        from institutions.models import Institution
        from parents.models import Parent
        from students.models import Student
        from subjects.models import Subject
        from teachers.models import Teacher
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        tables = connection.introspection.table_names()
        skip = {"django_content_type", "django_session", "django_admin_log", "auth_permission",
                "accounts_user_groups", "accounts_user_user_permissions"}
        for table in tables:
            if table in skip or table.startswith("django_") or table.startswith("auth_"):
                continue
            cursor.execute('DELETE FROM "{}"'.format(table))
        cursor.execute("PRAGMA foreign_keys = ON")
        User.objects.all().delete()

        import sys, io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

        self.stdout.write(self.style.SUCCESS("Database cleared. Seeding..."))

        # 1. Institution
        institution = Institution.objects.create(
            name="\u0645\u0639\u0647\u062f \u0627\u0644\u064a\u0631\u0645\u0648\u0643",
            short_name="\u0627\u0644\u064a\u0631\u0645\u0648\u0643",
            address="\u0634\u0627\u0631\u0639 \u0627\u0644\u0645\u0644\u0643 \u0641\u064a\u0635\u0644\u060c \u0628\u063a\u062f\u0627\u062f",
            phone_number="07701234567",
            email="al-yarmouk@school.edu",
        )
        self.stdout.write("  Institution: {}".format(institution.name))

        # 2. Manager user
        manager = User.objects.create_superuser(
            username="manager1",
            password="admin123",
            first_name="\u0623\u062d\u0645\u062f",
            last_name="\u0627\u0644\u0645\u062f\u064a\u0631",
            role="manager",
        )
        institution.users.add(manager)

        # 3. Teacher
        teacher_user = User.objects.create_user(
            username="teacher1",
            password="teacher123",
            first_name="\u0645\u062d\u0645\u062f",
            last_name="\u0639\u0644\u064a",
            role="teacher",
            gender="male",
        )
        teacher = Teacher.objects.create(
            user=teacher_user,
            institution=institution,
            employee_code="TCH0001",
            specialization="\u0631\u064a\u0627\u0636\u064a\u0627\u062a",
            phone_number="07709876543",
            hire_date=date(2020, 9, 1),
        )
        self.stdout.write("  Teacher: {}".format(teacher.user.get_full_name()))

        # 4. ClassRoom
        classroom = ClassRoom.objects.create(
            institution=institution,
            stage="primary",
            name="\u0627\u0644\u0635\u0641 \u0627\u0644\u0631\u0627\u0628\u0639",
            level="4",
            academic_year="2025-2026",
        )
        self.stdout.write("  ClassRoom: {}".format(classroom.name))

        # 5. Students
        student_male_user = User.objects.create_user(
            username="ali",
            password="student123",
            first_name="\u0639\u0644\u064a",
            last_name="\u062d\u0633\u064a\u0646",
            role="student",
            gender="male",
        )
        student1 = Student.objects.create(
            user=student_male_user,
            institution=institution,
            classroom=classroom,
            gender="male",
            student_code="STU0001",
            date_of_birth=date(2014, 3, 15),
            parent_phone="07701112233",
        )

        student_female_user = User.objects.create_user(
            username="huda",
            password="student123",
            first_name="\u0647\u062f\u0649",
            last_name="\u0645\u062d\u0645\u062f",
            role="student",
            gender="female",
        )
        student2 = Student.objects.create(
            user=student_female_user,
            institution=institution,
            classroom=classroom,
            gender="female",
            student_code="STU0002",
            date_of_birth=date(2014, 7, 22),
            parent_phone="07701112233",
        )
        self.stdout.write("  Students: {}, {}".format(
            student1.user.get_full_name(), student2.user.get_full_name()))

        # 6. Parent
        parent_user = User.objects.create_user(
            username="parent1",
            password="parent123",
            first_name="\u062d\u0633\u064a\u0646",
            last_name="\u0639\u0644\u064a",
            role="parent",
            gender="male",
        )
        parent = Parent.objects.create(
            user=parent_user,
            relationship="\u0623\u0628",
        )
        parent.students.add(student1, student2)
        self.stdout.write("  Parent: {}".format(parent.user.get_full_name()))

        # 7. Subjects
        subjects_data = [
            ("\u0631\u064a\u0627\u0636\u064a\u0627\u062a", "MATH001", "Arithmetic, algebra and geometry"),
            ("\u0639\u0644\u0648\u0645", "SCI001", "Natural science concepts"),
            ("\u0644\u063a\u0629 \u0639\u0631\u0628\u064a\u0629", "ARB001", "Arabic language and literature"),
            ("\u0625\u0646\u062c\u0644\u064a\u0632\u064a", "ENG001", "English language basics"),
        ]
        subject_objs = []
        for name, code, desc in subjects_data:
            subj = Subject.objects.create(
                institution=institution,
                name=name,
                code=code,
                description=desc,
                teacher=teacher,
                classroom=classroom,
            )
            subject_objs.append(subj)
        self.stdout.write("  Subjects: {}".format(", ".join(s.name for s in subject_objs)))

        # 8. Attendance (last 5 school days)
        today = date.today()
        statuses = ["present", "present", "late", "present", "absent"]
        for i in range(5):
            d = today - timedelta(days=i)
            if d.weekday() >= 5:
                continue
            for student in [student1, student2]:
                for subj in subject_objs:
                    try:
                        Attendance.objects.create(
                            student=student,
                            teacher=teacher,
                            subject=subj,
                            classroom=classroom,
                            date=d,
                            status=statuses[i % len(statuses)],
                        )
                    except Exception:
                        pass
        self.stdout.write("  Attendance records created")

        # 9. Grades
        exams = [
            ("\u0627\u062e\u062a\u0628\u0627\u0631 \u0627\u0644\u0641\u0635\u0644 \u0627\u0644\u0623\u0648\u0644", 85, 92),
            ("\u0627\u062e\u062a\u0628\u0627\u0631 \u0645\u0646\u062a\u0635\u0641 \u0627\u0644\u0641\u0635\u0644", 78, 88),
        ]
        for exam_name, score1, score2 in exams:
            for student, score in [(student1, score1), (student2, score2)]:
                for subj in subject_objs[:2]:
                    try:
                        Grade.objects.create(
                            student=student,
                            subject=subj,
                            teacher=teacher,
                            exam_name=exam_name,
                            score=score,
                            max_score=100,
                            exam_date=today - timedelta(days=30),
                        )
                    except Exception:
                        pass
        self.stdout.write("  Grades created")

        self.stdout.write(self.style.SUCCESS("\nSeed completed successfully!"))
        self.stdout.write("\n  Login accounts:")
        self.stdout.write("    admin   : admin123")
        self.stdout.write("    manager1: admin123")
        self.stdout.write("    teacher1: teacher123")
        self.stdout.write("    ali     : student123")
        self.stdout.write("    huda    : student123")
        self.stdout.write("    parent1 : parent123")
