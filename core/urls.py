from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("students.urls")),
    path("", RedirectView.as_view(url="/login/", permanent=False)),
]
