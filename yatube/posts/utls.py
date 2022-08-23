from django.conf import settings
from django.core.paginator import Paginator


def _add_paginator_page(request, instance, ):
    paginator = Paginator(instance, settings.COUNT_POST_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
