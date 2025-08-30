from django.urls import path

from accounts.views.authentication_views import LoginView, LogoutView
from accounts.views.dashboard_views import DashboardView
from accounts.views.group_views import GroupView
from accounts.views.staff_views import StaffView
from accounts.views.toggle_views import GenericToggleWithObjectPermissionView


app_name = "accounts"

urlpatterns = [
    # AUTHENTICATION
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # DASHBOARD
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # STAFF MANAGEMENT
    path("staffs/", StaffView.as_view(), name="staffs"),
    path("staffs/add/", StaffView.as_view(), name="staff-add"),
    path("staffs/<int:pk>/edit/", StaffView.as_view(), name="staff-edit"),
    path("staffs/<int:pk>/delete/", StaffView.as_view(), name="staff-delete"),

    # GROUP MANAGEMENT
    path("groups/", GroupView.as_view(), name="groups"),
    path("groups/add/", GroupView.as_view(), name="group-add"),
    path("groups/<int:pk>/edit/", GroupView.as_view(), name="group-edit"),
    path("groups/<int:pk>/delete/", GroupView.as_view(), name="group-delete"),
    path("groups/<int:pk>/permissions/", GroupView.as_view(), name="group-manage-permissions"),


    # toggle
     path('toggle/<str:model_name>/<int:pk>/', GenericToggleWithObjectPermissionView.as_view(), name='generic_toggle_field'),
]
