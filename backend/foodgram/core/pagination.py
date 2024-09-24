from rest_framework.pagination import (PageNumberPagination,
                                       LimitOffsetPagination)

from core.constants import Pagination


class PageSizePagination(PageNumberPagination):
    page_size = Pagination.PAGE_SIZE
    page_size_query_param = 'limit'


class PageSizeUserPagination(LimitOffsetPagination):
    page_size = Pagination.PAGE_SIZE
    page_size_query_param = 'limit'
