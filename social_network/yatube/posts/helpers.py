from django.core.paginator import Paginator

LIMIT = 10


def paginate(request, posts):
    paginator = Paginator(posts, LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
