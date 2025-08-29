
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class PaginatedListMixin:
    """Mixin to provide pagination functionality for list views"""
    
    paginate_by = 10  # Default items per page
    page_kwarg = 'page'
    
    def get_paginate_by(self):
        """Return the number of items to paginate by"""
        return getattr(self, 'paginate_by', 10)
    
    def get_queryset(self):
        """Override this method in subclasses to provide the queryset"""
        raise NotImplementedError("Subclasses must implement get_queryset method")
    
    def get_filtered_queryset(self, request):
        """Override this method in subclasses to provide filtering logic"""
        return self.get_queryset()
    
    def paginate_queryset(self, request, queryset):
        """Paginate the queryset"""
        paginate_by = self.get_paginate_by()
        paginator = Paginator(queryset, paginate_by)
        
        page = request.GET.get(self.page_kwarg)
        
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            page_obj = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            page_obj = paginator.page(paginator.num_pages)
        
        return page_obj, paginator
    
    def get_pagination_context(self, request, queryset):
        """Get pagination context for templates"""
        page_obj, paginator = self.paginate_queryset(request, queryset)
        
        return {
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': page_obj.has_other_pages(),
            'queryset': page_obj.object_list,
        }
