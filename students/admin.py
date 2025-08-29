
# Register your models here.
from django.contrib import admin
from .models import MetaData

@admin.register(MetaData)
class MetaDataAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('key', 'value')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    def value_preview(self, obj):
        return obj.value[:100] + '...' if len(obj.value) > 100 else obj.value
    value_preview.short_description = 'Value Preview'