from django.core.management.base import BaseCommand
from institutions.models import Institution
from classes.models import ClassRoom
from subjects.models import Subject
from teachers.models import Teacher
from students.models import Student
from parents.models import Parent


class Command(BaseCommand):
    help = "Link subjects to classrooms and teachers"

    def handle(self, *args, **options):
        institution = Institution.objects.first()
        if not institution:
            self.stdout.write(self.style.ERROR("No institution found. Run seed_data first."))
            return

        classrooms = list(ClassRoom.objects.filter(institution=institution))
        teachers = list(Teacher.objects.filter(institution=institution))
        subjects = list(Subject.objects.filter(institution=institution))
        students = list(Student.objects.filter(institution=institution))

        self.stdout.write(f"Found: {len(classrooms)} classrooms, {len(teachers)} teachers, {len(subjects)} subjects, {len(students)} students")

        classroom_subject_map = {}
        for i, subj in enumerate(subjects):
            cr = classrooms[i % len(classrooms)]
            subj.classroom = cr
            subj.save()
            classroom_subject_map[subj.name] = cr.name
            self.stdout.write(f"  Subject '{subj.name}' -> Classroom '{cr.name}'")

        teacher_subject_map = {}
        for i, subj in enumerate(subjects):
            if i < len(teachers):
                subj.teacher = teachers[i]
                subj.save()
                teacher_subject_map[subj.name] = f"{teachers[i].user.first_name} {teachers[i].user.last_name}"
                self.stdout.write(f"  Subject '{subj.name}' -> Teacher '{teacher_subject_map[subj.name]}'")

        student_classroom_map = {}
        for i, student in enumerate(students):
            cr = classrooms[i % len(classrooms)]
            student.classroom = cr
            student.save()
            student_classroom_map[f"{student.user.first_name} {student.user.last_name}"] = cr.name
            self.stdout.write(f"  Student '{student.user.first_name} {student.user.last_name}' -> Classroom '{cr.name}'")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("All relationships linked successfully!"))
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("SUMMARY:")
        self.stdout.write("=" * 50)
        for t in teachers:
            t_subjects = [s.name for s in subjects if s.teacher == t]
            t_classrooms = [s.classroom.name for s in subjects if s.teacher == t and s.classroom]
            self.stdout.write(f"Teacher: {t.user.first_name} {t.user.last_name}")
            self.stdout.write(f"  Subjects: {', '.join(t_subjects) or 'None'}")
            self.stdout.write(f"  Classrooms: {', '.join(set(t_classrooms)) or 'None'}")
            self.stdout.write("")

        for cr in classrooms:
            cr_students = [f"{s.user.first_name} {s.user.last_name}" for s in students if s.classroom == cr]
            cr_subjects = [s.name for s in subjects if s.classroom == cr]
            self.stdout.write(f"Classroom: {cr.name} - {cr.level}")
            self.stdout.write(f"  Students ({len(cr_students)}): {', '.join(cr_students) or 'None'}")
            self.stdout.write(f"  Subjects: {', '.join(cr_subjects) or 'None'}")
            self.stdout.write("")
