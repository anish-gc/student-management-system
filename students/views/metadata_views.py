import logging
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from students.forms.metadata_forms import MetaDataForm
from students.models.metadata_model import MetaData
from utilities.pagination_mixin import PaginatedListMixin
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

# Configure logger
logger = logging.getLogger(__name__)


class MetaDataView(LoginRequiredMixin, PaginatedListMixin, View):
    """MetaData view for listing, adding, editing, and deleting metadata"""
    login_url = '/login/'           
    redirect_field_name = 'next'            
    paginate_by = 15  # Override default pagination

    def get(self, request, pk=None):
        """Handle GET requests based on URL name"""
        if request.resolver_match.url_name == 'metadata-add':
            return self.add_metadata(request)
        elif request.resolver_match.url_name == 'metadata-edit' and pk:
            return self.edit_metadata(request, pk)
        elif request.resolver_match.url_name == 'metadata-delete' and pk:
            return self.delete_metadata(request, pk)
      
        else:
            return self.metadata_list(request)

    def post(self, request, pk=None):
        """Handle POST requests based on URL name"""
        if request.resolver_match.url_name == 'metadata-add':
            return self.add_metadata_submit(request)
        elif request.resolver_match.url_name == 'metadata-edit' and pk:
            return self.edit_metadata_submit(request, pk)
        elif request.resolver_match.url_name == 'metadata-delete' and pk:
            return self.delete(request, pk)
        return redirect("utilities:metadata")

    def delete(self, request, pk=None):
        """Handle DELETE requests for metadata deletion"""
        if pk:
            return self.delete_metadata(request, pk)
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    def get_queryset(self):
        """Get base queryset for metadata"""
        return MetaData.objects.all()

    def get_filtered_queryset(self, request):
        """Apply filters to the queryset"""
        queryset = self.get_queryset()

        # Key filter
        key_filter = request.GET.get("key")
        if key_filter:
            queryset = queryset.filter(key__icontains=key_filter)

        # Value filter
        value_filter = request.GET.get("value")
        if value_filter:
            queryset = queryset.filter(value__icontains=value_filter)

        # Status filter
        status_filter = request.GET.get("status")
        if status_filter:
            is_active = status_filter.lower() == "active"
            queryset = queryset.filter(is_active=is_active)

        # Search filter
        search_query = request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(key__icontains=search_query)
                | Q(value__icontains=search_query)
            )

        return queryset.distinct().order_by("-created_at")
    @method_decorator(permission_required("students.view_metadata", raise_exception=True))

    def metadata_list(self, request):
        """Display paginated list of metadata"""
        # Get filtered queryset
        filtered_queryset = self.get_filtered_queryset(request)

        # Get pagination context
        pagination_context = self.get_pagination_context(request, filtered_queryset)

        # Additional context
        context = {
            **pagination_context,
            "current_filters": {
                "key": request.GET.get("key", ""),
                "value": request.GET.get("value", ""),
                "status": request.GET.get("status", ""),
                "search": request.GET.get("search", ""),
            },
        }

        return render(request, "students/metadata/metadata_list.html", context)
    @method_decorator(permission_required("students.add_metadata", raise_exception=True))

    def add_metadata(self, request):
        """Display add metadata form"""
        form = MetaDataForm()
        context = {
            "form": form,
            "is_adding": True,
            "page_title": "Add Metadata",
        }
        return render(request, "students/metadata/metadata_form.html", context)
    @method_decorator(permission_required("students.add_metadata", raise_exception=True))

    def add_metadata_submit(self, request):
        """Process add metadata form submission"""
        form = MetaDataForm(request.POST)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                # Create the metadata
                metadata = form.save()
                success_message = f"Metadata '{metadata.key}' added successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:metadata")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("utilities:metadata")

            except Exception as e:
                error_message = f"Error adding metadata: {str(e)}"
                logger.error(error_message)

                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {}
                for field_name, field_errors in form.errors.items():
                    errors[field_name] = [str(error) for error in field_errors]

                return JsonResponse(
                    {
                        "success": False,
                        "errors": errors,
                        "message": "Please correct the errors below.",
                    },
                    status=400,
                )
            else:
                messages.error(request, "Please correct the errors below.")

        # If we reach here and it's not AJAX, render the form with errors
        if not is_ajax:
            context = {
                "form": form,
                "is_adding": True,
                "page_title": "Add Metadata",
            }
            return render(request, "students/metadata/metadata_form.html", context)
    @method_decorator(permission_required("students.change_metadata", raise_exception=True))

    def edit_metadata(self, request, pk):
        """Display edit metadata form"""
        metadata = get_object_or_404(MetaData, pk=pk)
        form = MetaDataForm(instance=metadata)

        context = {
            "form": form,
            "metadata_obj": metadata,
            "is_editing": True,
            "page_title": f"Edit Metadata: {metadata.key}",
        }
        return render(request, "students/metadata/metadata_form.html", context)
    @method_decorator(permission_required("students.change_metadata", raise_exception=True))

    def edit_metadata_submit(self, request, pk):
        """Process edit metadata form submission"""
        metadata = get_object_or_404(MetaData, pk=pk)
        form = MetaDataForm(request.POST, instance=metadata)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if form.is_valid():
            try:
                metadata = form.save()
                success_message = f"Metadata '{metadata.key}' updated successfully!"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": success_message,
                            "redirect_url": request.build_absolute_uri(
                                reverse("students:metadata")
                            ),
                        }
                    )
                else:
                    messages.success(request, success_message)
                    return redirect("students:metadata")

            except Exception as e:
                error_message = f"Error updating metadata: {str(e)}"
                logger.error(error_message)

                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_message}, status=500
                    )
                else:
                    messages.error(request, error_message)
        else:
            # Form validation failed
            if is_ajax:
                errors = {}
                for field_name, field_errors in form.errors.items():
                    errors[field_name] = [str(error) for error in field_errors]

                return JsonResponse(
                    {
                        "success": False,
                        "errors": errors,
                        "message": "Please correct the errors below.",
                    },
                    status=400,
                )
            else:
                messages.error(request, "Please correct the errors below.")

        # If we reach here and it's not AJAX, render the form with errors
        if not is_ajax:
            context = {
                "form": form,
                "metadata_obj": metadata,
                "is_editing": True,
                "page_title": f"Edit Metadata: {metadata.key}",
            }
            return render(request, "students/metadata/metadata_form.html", context)
    @method_decorator(permission_required("students.delete_metadata", raise_exception=True))

    def delete_metadata(self, request, pk):
        """Delete a metadata entry"""
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            metadata = get_object_or_404(MetaData, pk=pk)
            metadata_key = metadata.key
            metadata.delete()
            
            success_message = f"Metadata '{metadata_key}' deleted successfully!"

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "message": success_message,
                        "redirect": reverse('students:metadata')
                    }
                )
            else:
                messages.success(request, success_message)
                return redirect("students:metadata")

        except Exception as e:
            error_message = f"Error deleting metadata: {str(e)}"
            logger.error(error_message)

            if is_ajax:
                return JsonResponse(
                    {"success": False, "error": error_message}, status=500
                )
            else:
                messages.error(request, error_message)
                return redirect("students:metadata")