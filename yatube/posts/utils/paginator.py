from django.core.paginator import Paginator

from yatube.settings import POSTS_PER_PAGE


def paginator(queryset, request):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    get_obj = paginator.get_page(page_number)
    return get_obj
