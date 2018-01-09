from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'

    # this is the size for the CSV renderer
    # Total number of rows on a worksheet (since Excel 2007): 1048576 (remove one for the header)
    # https://support.office.com/en-us/article/Excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3
    max_page_size = 1048575
