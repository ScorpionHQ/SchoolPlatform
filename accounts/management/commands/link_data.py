import datetime
from django.core.management.base import BaseCommand
from institutions.models import Institution
from classes.models import ClassRoom
from subjects.models import Subject
from teachers.models import Teacher
from students.models import Student
from grades.models import Grade
from attendance.models import Attendance


class Command(BaseCommand):
    help = "Link all students to all teachers, subjects, and classrooms with grades & attendance"

    def handle(self, *args, **options):
        institution = Institution.objects.first()
        if not institution:
            self.stdout.write(self.style.ERROR("No institution found. Run seed_data first."))
            return

        classrooms = list(ClassRoom.objects.filter(institution=institution))
        teachers = list(Teacher.objects.filter(institution=institution))
        subjects = list(Subject.objects.filter(institution=institution))
        students = list(Student.objects.filter(institution=institution))

        if not classrooms or not teachers or not subjects or not students:
            self.stdout.write(self.style.ERROR("Missing data. Run seed_data first."))
            return

        self.stdout.write(f"Found: {len(classrooms)} classrooms, {len(teachers)} teachers, {len(subjects)} subjects, {len(students)} students")
        self.stdout.write("")

        self.stdout.write("--- Linking Subjects to Classrooms ---")
        for subj in subjects:
            subj.classroom = None
            subj.save()
        for i, subj in enumerate(subjects):
            subj.classroom = classrooms[i % len(classrooms)]
            subj.save()
            self.stdout.write(f"  '{subj.name}' -> '{subj.classroom.name}'")

        self.stdout.write("")
        self.stdout.write("--- Linking Subjects to Teachers ---")
        for i, subj in enumerate(subjects):
            subj.teacher = teachers[i % len(teachers)]
            subj.save()
            self.stdout.write(f"  '{subj.name}' -> {subj.teacher.user.first_name} {subj.teacher.user.last_name}")

        self.stdout.write("")
        self.stdout.write("--- Assigning Students to Classrooms ---")
        for i, student in enumerate(students):
            student.classroom = classrooms[i % len(classrooms)]
            student.save()
            self.stdout.write(f"  {student.user.first_name} {student.user.last_name} -> {student.classroom.name}")

        self.stdout.write("")
        self.stdout.write("--- Creating Attendance Records ---")
        today = datetime.date.today()
        statuses = ["present", "present", "present", "absent", "late", "excused"]
        attendance_count = 0
        for student in students:
            for subj in subjects:
                for day_offset in range(7):
                    date = today - datetime.timedelta(days=day_offset)
                    if date.weekday() >= 5:
                        continue
                    _, created = Attendance.objects.get_or_create(
                        student=student,
                        subject=subj,
                        date=date,
                        defaults={
                            "teacher": subj.teacher,
                            "classroom": student.classroom,
                            "status": statuses[day_offset % len(statuses)],
                        },
                    )
                    if created:
                        attendance_count += 1
        self.stdout.write(f"  Created {attendance_count} attendance records")

        self.stdout.write("")
        self.stdout.write("--- Creating Grade Records ---")
        exam_names = ["اختبار شهري 1", "اختبار شهري 2", "امتحان الفصل الأول", "امتحان الفصل الثاني"]
        grade_count = 0
        for student in students:
            for subj in subjects:
                for j, exam in enumerate(exam_names):
                    _, created = Grade.objects.get_or_create(
                        student=student,
                        subject=subj,
                        exam_name=exam,
                        defaults={
                            "teacher": subj.teacher,
                            "score": 65 + (j * 8),
                            "max_score": 100,
                            "exam_date": today - datetime.timedelta(days=30 * (4 - j)),
                        },
                    )
                    if created:
                        grade_count += 1
        self.stdout.write(f"  Created {grade_count} grade records")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("ALL RELATIONSHIPS LINKED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        for t in teachers:
            t_subjects = [s.name for s in subjects if s.teacher == t]
            t_classrooms = list(set(s.classroom.name for s in subjects if s.teacher == t and s.classroom))
            self.stdout.write(f"Teacher: {t.user.first_name} {t.user.last_name} ({t.employee_code})")
            self.stdout.write(f"  Subjects: {', '.join(t_subjects)}")
            self.stdout.write(f"  Classrooms: {', '.join(t_classrooms)}")
            student_count = len(students)
            self.stdout.write(f"  Students linked: {student_count}")
            self.stdout.write("")

        for cr in classrooms:
            cr_students = [f"{s.user.first_name} {s.user.last_name}" for s in students if s.classroom == cr]
            cr_subjects = [f"{s.name} ({s.teacher.user.first_name})" for s in subjects if s.classroom == cr]
            self.stdout.write(f"Classroom: {cr.name} - {cr.level}")
            self.stdout.write(f"  Students ({len(cr_students)}): {', '.join(cr_students)}")
            self.stdout.write(f"  Subjects: {', '.join(cr_subjects)}")
            self.stdout.write("")
