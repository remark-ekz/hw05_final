from django.core.paginator import Paginator

POSTS_ON_PAGE = 10


def paginator_view(post_list, request):
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
