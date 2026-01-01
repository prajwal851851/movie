from rest_framework.pagination import CursorPagination, PageNumberPagination


class CursorPaginationExample(PageNumberPagination):
    page_size=100
    page_size_query_param='page_size'
    max_page_size = 100
    
    # Custom query parameter name for page number
    page_query_param = 'page'
    
    # Show last page link in response
    last_page_strings = ('last',)

