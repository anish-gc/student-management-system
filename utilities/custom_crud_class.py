# base_views.py
import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class BaseCRUDView(LoginRequiredMixin, PaginatedListMixin, View):
    """Base CRUD view with common functionality"""
    
    # Class attributes that must be overridden in subclasses
    model = None
    form_class = None
    template_base = None  # e.g., 'students/students'
    url_namespace = None  # e.g., 'students'
    url_name_base = None  # e.g., 'student'
    
    # Optional attributes with defaults
    login_url = "/login/"
    redirect_field_name = "next"
    paginate_by = 15
    
    # Permission-related attributes
    view_permission = None
    add_permission = None
    change_permission = None
    delete_permission = None
    
    # Context and display customization
    list_context_extras = {}
    form_context_extras = {}
    
    def get_permissions(self):
        """Get permission strings based on model"""
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        
        return {
            'view': self.view_permission or f"{app_label}.view_{model_name}",
            'add': self.add_permission or f"{app_label}.add_{model_name}",
            'change': self.change_permission or f"{app_label}.change_{model_name}",
            'delete': self.delete_permission or f"{app_label}.delete_{model_name}",
        }
    
    def get_url_names(self):
        """Get URL names based on url_name_base"""
        base = self.url_name_base
        return {
            'list': f"{base}s",
            'add': f"{base}-add",
            'edit': f"{base}-edit",
            'delete': f"{base}-delete",
        }
    
    def get_templates(self):
        """Get template names based on template_base"""
        base = self.template_base
        return {
            'list': f"{base}_list.html",
            'form': f"{base}_form.html",
        }
    
    def get_success_message(self, action, obj):
        """Generate success message for CRUD operations"""
        obj_name = getattr(obj, 'name', None) or str(obj)
        messages = {
            'add': f"{self.model._meta.verbose_name.title()} '{obj_name}' added successfully!",
            'edit': f"{self.model._meta.verbose_name.title()} '{obj_name}' updated successfully!",
            'delete': f"{self.model._meta.verbose_name.title()} '{obj_name}' deleted successfully!",
        }
        return messages.get(action, f"Operation completed successfully!")
    
    def get_error_message(self, action, error):
        """Generate error message for CRUD operations"""
        return f"Error {action}ing {self.model._meta.verbose_name}: {str(error)}"
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to check permissions before routing"""
        # Store request for permission checking
        self.request = request
        
        # Get the URL name and determine required permission
        url_name = request.resolver_match.url_name
        url_names = self.get_url_names()
       
        permissions = self.get_permissions()
        # Determine which permission is needed
        required_permission = None
        if url_name == url_names['list']:
            required_permission = permissions['view']
        elif url_name == url_names['add']:
            required_permission = permissions['add']
        elif url_name in [url_names['edit'], url_names['delete']]:
            if url_name == url_names['edit']:
                required_permission = permissions['change']
            else:  # delete
                required_permission = permissions['delete']
        
        # Check permission if required
        if required_permission and not request.user.has_perm(required_permission):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        url_name = request.resolver_match.url_name
        url_names = self.get_url_names()
        if url_name == url_names['add']:
            return self.add_view(request)
        elif url_name == url_names['edit'] and pk:
            return self.edit_view(request, pk)
        elif url_name == url_names['delete'] and pk:
            return self.delete_view(request, pk)
        else:
            return self.list_view(request)
    
    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        url_name = request.resolver_match.url_name
        url_names = self.get_url_names()
        
        if url_name == url_names['add']:
            return self.add_submit(request)
        elif url_name == url_names['edit'] and pk:
            return self.edit_submit(request, pk)
        elif url_name == url_names['delete'] and pk:
            return self.delete_submit(request, pk)
        
        return redirect(f"{self.url_namespace}:{url_names['list']}")
    
    def delete(self, request, pk=None):
        """Handle DELETE requests"""
        if pk:
            return self.delete_submit(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
    
    def get_queryset(self):
        """Get base queryset - override in subclasses if needed"""
        return self.model.objects.all()
    
    def get_filtered_queryset(self, request):
        """Apply filters to queryset - override in subclasses"""
        return self.get_queryset()
    
    def get_list_context_data(self, request, pagination_context):
        """Get additional context for list view - override in subclasses"""
        return self.list_context_extras.copy()
    
    def get_form_context_data(self, request, form, obj=None, is_editing=False):
        """Get additional context for form view - override in subclasses"""
        context = self.form_context_extras.copy()
        context.update({
            'form': form,
            'is_editing': is_editing,
            'is_adding': not is_editing,
        })
        
        if obj:
            obj_name = f"{self.model._meta.model_name}_obj"
            context[obj_name] = obj
            context['page_title'] = f"Edit {self.model._meta.verbose_name.title()}: {obj}"
        else:
            context['page_title'] = f"Add {self.model._meta.verbose_name.title()}"
        
        return context
    
    def process_form_save(self, form, obj=None):
        """Process form save with any additional logic - override in subclasses"""
        instance = form.save(commit=False)
        
        # Set default values if creating new object
        if not obj and hasattr(instance, 'is_active'):
            instance.is_active = True
        
        instance.save()
        
        # Handle many-to-many relationships
        if hasattr(form, 'save_m2m'):
            form.save_m2m()
        
        return instance
    
    def can_delete_object(self, obj):
        """Check if object can be deleted - override in subclasses"""
        return True, None  # (can_delete, error_message)
    
    def list_view(self, request):
        """Display paginated list"""
        filtered_queryset = self.get_filtered_queryset(request)
        pagination_context = self.get_pagination_context(request, filtered_queryset)
        
        context = {
            **pagination_context,
            **self.get_list_context_data(request, pagination_context),
        }
        
        templates = self.get_templates()
        return render(request, templates['list'], context)
    
    def add_view(self, request):
        """Display add form"""
        form = self.form_class()
        context = self.get_form_context_data(request, form, is_editing=False)
        
        templates = self.get_templates()
        return render(request, templates['form'], context)
    
    def add_submit(self, request):
        """Process add form submission"""
        form = self.form_class(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        
        if form.is_valid():
            try:
                obj = self.process_form_save(form)
                success_message = self.get_success_message('add', obj)
                url_names = self.get_url_names()
                
                if is_ajax:
                    return JsonResponse({
                        "success": True,
                        "message": success_message,
                        "redirect_url": request.build_absolute_uri(
                            reverse(f"{self.url_namespace}:{url_names['list']}")
                        ),
                    })
                else:
                    messages.success(request, success_message)
                    return redirect(f"{self.url_namespace}:{url_names['list']}")
                    
            except Exception as e:
                error_message = self.get_error_message('add', e)
                logger.error(f"Error adding {self.model._meta.verbose_name}: {e}")
                
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {
                    field_name: [str(error) for error in field_errors]
                    for field_name, field_errors in form.errors.items()
                }
                return JsonResponse({
                    "success": False,
                    "errors": errors,
                    "message": "Please correct the errors below.",
                }, status=400)
            else:
                messages.error(request, "Please correct the errors below.")
        
        # Re-render form with errors
        if not is_ajax:
            context = self.get_form_context_data(request, form, is_editing=False)
            templates = self.get_templates()
            return render(request, templates['form'], context)
    
    def edit_view(self, request, pk):
        """Display edit form"""
        obj = get_object_or_404(self.model, pk=pk)
        form = self.form_class(instance=obj)
        context = self.get_form_context_data(request, form, obj=obj, is_editing=True)
        templates = self.get_templates()
        return render(request, templates['form'], context)
    
    def edit_submit(self, request, pk):
        """Process edit form submission"""
        obj = get_object_or_404(self.model, pk=pk)
        form = self.form_class(request.POST, instance=obj)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        
        if form.is_valid():
            try:
                updated_obj = self.process_form_save(form, obj)
                success_message = self.get_success_message('edit', updated_obj)
                url_names = self.get_url_names()
                
                if is_ajax:
                    return JsonResponse({
                        "success": True,
                        "message": success_message,
                        "redirect_url": request.build_absolute_uri(
                            reverse(f"{self.url_namespace}:{url_names['list']}")
                        ),
                    })
                else:
                    messages.success(request, success_message)
                    return redirect(f"{self.url_namespace}:{url_names['list']}")
                    
            except Exception as e:
                error_message = self.get_error_message('edit', e)
                logger.error(f"Error updating {self.model._meta.verbose_name}: {e}")
                
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {
                    field_name: [str(error) for error in field_errors]
                    for field_name, field_errors in form.errors.items()
                }
                return JsonResponse({
                    "success": False,
                    "errors": errors,
                    "message": "Please correct the errors below.",
                }, status=400)
            else:
                messages.error(request, "Please correct the errors below.")
        
        # Re-render form with errors
        if not is_ajax:
            context = self.get_form_context_data(request, form, obj=obj, is_editing=True)
            templates = self.get_templates()
            return render(request, templates['form'], context)
    
    def delete_view(self, request, pk):
        """Handle delete view (if needed for confirmation page)"""
        return self.delete_submit(request, pk)
    
    def delete_submit(self, request, pk):
        """Delete an object"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        
        try:
            obj = get_object_or_404(self.model, pk=pk)
            
            # Check if deletion is allowed
            can_delete, error_msg = self.can_delete_object(obj)
            if not can_delete:
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_msg}, status=400
                    )
                else:
                    messages.error(request, error_msg)
                    return redirect(f"{self.url_namespace}:{self.get_url_names()['list']}")
            
            obj_name = str(obj)
            obj.delete()
            success_message = self.get_success_message('delete', type('obj', (), {'name': obj_name})())
            url_names = self.get_url_names()
            
            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "message": success_message,
                    "redirect": reverse(f"{self.url_namespace}:{url_names['list']}"),
                })
            else:
                messages.success(request, success_message)
                return redirect(f"{self.url_namespace}:{url_names['list']}")
                
        except Exception as e:
            error_message = self.get_error_message('delete', e)
            logger.error(f"Error deleting {self.model._meta.verbose_name}: {e}")
            
            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect(f"{self.url_namespace}:{self.get_url_names()['list']}")


# mixins.py
class FilterMixin:
    """Mixin for common filtering functionality"""
    
    search_fields = []  # Fields to search in
    filter_fields = {}  # {filter_param: field_lookup}
    
    def apply_search_filter(self, queryset, search_query):
        """Apply search filter across specified fields"""
        if not search_query or not self.search_fields:
            return queryset
        
        search_q = Q()
        for field in self.search_fields:
            search_q |= Q(**{f"{field}__icontains": search_query})
        
        return queryset.filter(search_q)
    
    def apply_field_filters(self, queryset, request):
        """Apply field-specific filters"""
        for param, field_lookup in self.filter_fields.items():
            value = request.GET.get(param)
            if value:
                # Handle boolean filters
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                queryset = queryset.filter(**{field_lookup: value})
        
        return queryset
    
    def get_filtered_queryset(self, request):
        """Apply all filters to queryset"""
        queryset = self.get_queryset()
        
        # Apply field filters
        queryset = self.apply_field_filters(queryset, request)
        
        # Apply search filter
        search_query = request.GET.get("search")
        queryset = self.apply_search_filter(queryset, search_query)
        
        return queryset.distinct().order_by(self.get_default_ordering())
    
    def get_default_ordering(self):
        """Get default ordering for queryset"""
        return "-created_at" if hasattr(self.model, 'created_at') else "id"
    
    def get_current_filters(self, request):
        """Get current filter values for template context"""
        filters = {"search": request.GET.get("search", "")}
        for param in self.filter_fields.keys():
            filters[param] = request.GET.get(param, "")
        return filters


class MetadataMixin:
    """Mixin for models that have metadata relationships"""
    
    def get_form_context_data(self, request, form, obj=None, is_editing=False):
        context = super().get_form_context_data(request, form, obj, is_editing)
        
        # Add metadata list if the model has metadata field
        if hasattr(self.model, 'metadata'):
            from students.models.metadata_model import MetaData
            context['metadata_list'] = MetaData.objects.all()
        
        return context


class ManyToManyMixin:
    """Mixin for handling many-to-many relationships in forms"""
    
    def process_form_save(self, form, obj=None):
        """Override to handle many-to-many relationships"""
        instance = super().process_form_save(form, obj)
        
        # Handle many-to-many fields
        for field_name, field in form.fields.items():
            if hasattr(field, 'queryset') and hasattr(instance, field_name):
                field_data = form.cleaned_data.get(field_name)
                if field_data is not None:
                    getattr(instance, field_name).set(field_data)
        
        return instance