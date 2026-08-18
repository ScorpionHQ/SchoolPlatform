from .models import Student


class StudentSelector:

    @staticmethod
    def get_all():

        return (
            Student.objects
            .select_related(
                "user",
                "institution",
                "classroom",
            )
            .order_by("student_code")
        )