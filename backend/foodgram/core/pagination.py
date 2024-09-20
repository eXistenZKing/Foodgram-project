from core.constants import Pagination
from rest_framework.pagination import PageNumberPagination


class PageSizePagination(PageNumberPagination):
    page_size = Pagination.PAGE_SIZE
    page_size_query_param = "limit"
