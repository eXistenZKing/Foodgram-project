from rest_framework.pagination import PageNumberPagination

from ..core.constants import Pagination


class PageSizePagination(PageNumberPagination):
    page_size = Pagination.PAGE_SIZE
    page_size_query_param = "limit"
