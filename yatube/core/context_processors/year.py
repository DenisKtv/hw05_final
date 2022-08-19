from django.utils import timezone


def year(request):
    now = timezone.now()
    year = now.year
    return {
        'year': year,
    }
