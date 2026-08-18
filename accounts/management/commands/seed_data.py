import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import User
from institutions.models import Institution
from classes.models import ClassRoom
from subjects.models import Subject
from teachers.models import Teacher
from students.models import Student
from parents.models import Parent
from grades.models import Grade
from attendance.models import Attendance

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        institution, _ = Institution.objects.get_or_create(
            name="مدرسة النور للبنين",
            defaults={
                "short_name": "النور",
                "address": "نينوى - الموصل",
                "phone_number": "07701234567",
                "email": "alnoor@example.com",
            },
        )

        classrooms_data = [
            {"stage": "primary", "name": "الصف الأول", "level": "الأول", "academic_year": "2025-2026"},
            {"stage": "primary", "name": "الصف الثاني", "level": "الثاني", "academic_year": "2025-2026"},
            {"stage": "primary", "name": "الصف الثالث", "level": "الثالث", "academic_year": "2025-2026"},
        ]
        classrooms = []
        for cd in classrooms_data:
            cr, _ = ClassRoom.objects.get_or_create(
                institution=institution,
                name=cd["name"],
                level=cd["level"],
                academic_year=cd["academic_year"],
                defaults={"stage": cd["stage"]},
            )
            classrooms.append(cr)

        subjects_data = [
            {"name": "الرياضيات", "code": "MATH-101", "classroom_idx": 0},
            {"name": "اللغة العربية", "code": "ARB-101", "classroom_idx": 0},
            {"name": "اللغة الإنجليزية", "code": "ENG-101", "classroom_idx": 1},
            {"name": "العلوم", "code": "SCI-101", "classroom_idx": 1},
            {"name": "التربية الإسلامية", "code": "ISL-101", "classroom_idx": 2},
            {"name": "التاريخ", "code": "HIS-101", "classroom_idx": 2},
        ]
        subjects = []
        for sd in subjects_data:
            s, _ = Subject.objects.get_or_create(
                institution=institution,
                code=sd["code"],
                defaults={
                    "name": sd["name"],
                    "classroom": classrooms[sd["classroom_idx"]],
                },
            )
            subjects.append(s)

        teachers_data = [
            {"first": "أحمد", "last": "محمد", "spec": "الرياضيات", "phone": "07701111111"},
            {"first": "فاطمة", "last": "علي", "spec": "اللغة العربية", "phone": "07702222222"},
            {"first": "خالد", "last": "حسين", "spec": "اللغة الإنجليزية", "phone": "07703333333"},
            {"first": "نور", "last": "الدين", "spec": "العلوم", "phone": "07704444444"},
        ]
        teachers = []
        for i, td in enumerate(teachers_data, 1):
            username = f"teacher{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": td["first"],
                    "last_name": td["last"],
                    "role": User.Role.TEACHER,
                    "gender": User.Gender.MALE if i % 2 == 1 else User.Gender.FEMALE,
                    "phone_number": td["phone"],
                },
            )
            if created:
                user.set_password("teacher123")
                user.save()
            teacher, _ = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    "institution": institution,
                    "employee_code": f"TCH{i:06d}",
                    "specialization": td["spec"],
                    "phone_number": td["phone"],
                    "hire_date": datetime.date(2024, 9, 1),
                },
            )
            teachers.append(teacher)

        for i, teacher in enumerate(teachers):
            if i < len(subjects):
                subjects[i].teacher = teacher
                subjects[i].save()

        students_data = [
            {"first": "علي", "last": "أحمد", "gender": "male", "parent_phone": "07705555551", "dob": "2015-03-10", "classroom": 0},
            {"first": "محمد", "last": "كريم", "gender": "male", "parent_phone": "07705555552", "dob": "2015-06-22", "classroom": 0},
            {"first": "يوسف", "last": "عمر", "gender": "male", "parent_phone": "07705555553", "dob": "2014-01-15", "classroom": 1},
            {"first": "حسن", "last": "نوري", "gender": "male", "parent_phone": "07705555554", "dob": "2014-08-05", "classroom": 1},
            {"first": "عمر", "last": "سامي", "gender": "male", "parent_phone": "07705555555", "dob": "2013-04-18", "classroom": 2},
            {"first": "أحمد", "last": "جلال", "gender": "male", "parent_phone": "07705555556", "dob": "2013-11-30", "classroom": 2},
            {"first": "زياد", "last": "حسن", "gender": "male", "parent_phone": "07705555557", "dob": "2015-09-12", "classroom": 0},
            {"first": "ياسر", "last": "محمود", "gender": "male", "parent_phone": "07705555558", "dob": "2014-02-25", "classroom": 1},
        ]
        students = []
        for i, sd in enumerate(students_data, 1):
            username = f"student{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": sd["first"],
                    "last_name": sd["last"],
                    "role": User.Role.STUDENT,
                    "gender": sd["gender"],
                    "phone_number": sd["parent_phone"],
                },
            )
            if created:
                user.set_password("student123")
                user.save()
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    "institution": institution,
                    "classroom": classrooms[sd["classroom"]],
                    "gender": sd["gender"],
                    "student_code": f"STU{i:06d}",
                    "date_of_birth": datetime.date.fromisoformat(sd["dob"]),
                    "parent_phone": sd["parent_phone"],
                },
            )
            students.append(student)

        parents_data = [
            {"first": "أحمد", "last": "علي", "phone": "07705555551", "relationship": "أب", "student_indices": [0, 1]},
            {"first": "عمر", "last": "يوسف", "phone": "07705555553", "relationship": "أب", "student_indices": [2, 3]},
            {"first": "سامي", "last": "عمر", "phone": "07705555555", "relationship": "أب", "student_indices": [4, 5]},
            {"first": "محمود", "last": "ياسر", "phone": "07705555558", "relationship": "أب", "student_indices": [7]},
        ]
        for i, pd in enumerate(parents_data, 1):
            username = f"parent{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": pd["first"],
                    "last_name": pd["last"],
                    "role": User.Role.PARENT,
                    "gender": User.Gender.MALE,
                    "phone_number": pd["phone"],
                },
            )
            if created:
                user.set_password("parent123")
                user.save()
            parent, _ = Parent.objects.get_or_create(
                user=user,
                defaults={"relationship": pd["relationship"]},
            )
            for idx in pd["student_indices"]:
                parent.students.add(students[idx])

        today = datetime.date.today()
        statuses = ["present", "absent", "late", "excused"]
        for student in students[:4]:
            for subj in subjects[:3]:
                for day_offset in range(5):
                    date = today - datetime.timedelta(days=day_offset)
                    if date.weekday() >= 5:
                        continue
                    Attendance.objects.get_or_create(
                        student=student,
                        subject=subj,
                        classroom=student.classroom,
                        date=date,
                        defaults={
                            "teacher": teachers[0],
                            "status": statuses[day_offset % 4],
                        },
                    )

        exam_names = ["امتحان الفصل الأول", "امتحان الفصل الثاني", "اختبار شهري"]
        for student in students[:4]:
            for subj in subjects[:3]:
                for j, exam in enumerate(exam_names):
                    Grade.objects.get_or_create(
                        student=student,
                        subject=subj,
                        exam_name=exam,
                        defaults={
                            "teacher": teachers[0],
                            "score": 70 + (j * 5),
                            "max_score": 100,
                            "exam_date": today - datetime.timedelta(days=30 * (3 - j)),
                        },
                    )

        self.stdout.write(self.style.SUCCESS("Done! Database seeded successfully."))
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("ACCOUNTS CREDENTIALS:")
        self.stdout.write("=" * 50)
        self.stdout.write("MANAGER / ADMIN:")
        self.stdout.write("  Username: rayyan_20nadmin")
        self.stdout.write("  Password: (the one you set)")
        self.stdout.write("")
        self.stdout.write("TEACHERS:")
        for i in range(1, 5):
            user = User.objects.get(username=f"teacher{i}")
            self.stdout.write(f"  {user.first_name} {user.last_name} | Login: {user.login_code} | Username: teacher{i} | Password: teacher123")
        self.stdout.write("")
        self.stdout.write("STUDENTS:")
        for i in range(1, 9):
            user = User.objects.get(username=f"student{i}")
            self.stdout.write(f"  {user.first_name} {user.last_name} | Login: {user.login_code} | Username: student{i} | Password: student123")
        self.stdout.write("")
        self.stdout.write("PARENTS:")
        for i in range(1, 5):
            user = User.objects.get(username=f"parent{i}")
            self.stdout.write(f"  {user.first_name} {user.last_name} | Login: {user.login_code} | Username: parent{i} | Password: parent123")
        self.stdout.write("=" * 50)
