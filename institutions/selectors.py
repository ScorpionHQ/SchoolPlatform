from .models import Institution


class InstitutionSelector:

    @staticmethod
    def get_all():

        return Institution.objects.order_by("name")