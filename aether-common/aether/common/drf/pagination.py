from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    # this is the size for the CSV renderer
    max_page_size = 10000
