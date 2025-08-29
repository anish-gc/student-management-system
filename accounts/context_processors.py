
from django.urls import reverse

# context_processors.py
from django.urls import reverse

def sidebar_processor(request):
    """
    Context processor to generate dynamic sidebar based on user roles and permissions
    """
    if not request.user.is_authenticated:
        return {"sidebar_menu": []}

    user = request.user

    # Define your complete sidebar structure with required permissions
    SIDEBAR_CONFIG = [
        {
            "name": "Dashboard",
            "icon": "fas fa-tachometer-alt",
            "url_name": "accounts:dashboard",
            "permission": 'accounts.view_dashboard',
            "is_header": False,
        },
        {
            "name": "Account Management",
            "icon": "",
            "permission": "auth.view_user",
            "is_header": True,
            "children": [
                {
                    "name": "Groups",
                    "icon": "far fa-user",
                    "url_name": "accounts:groups",
                    "permission": "auth.view_group",
                },
                {
                    "name": "Staffs",
                    "icon": "far fa-user",
                    "url_name": "accounts:staffs",
                    "permission": "auth.view_user",
                },
                {
                    "name": "Students",
                    "icon": "far fa-user",
                    "url_name": "students:students",
                    "permission": "students.view_student",
                },
                {
                    "name": "Instructor",
                    "icon": "far fa-user",
                    "url_name": "students:instructors",
                    "permission": "students.view_instructor",
                },
            ],
        },
        {
            "name": "Course Management",
            "icon": "",
            "permission": "students.view_course",
            "is_header": True,
            "children": [
                {
                    "name": "Courses",
                    "icon": "far fa-user",
                    "url_name": "students:courses",
                    "permission": "students.view_course",
                },
            ],
        },
        {
            "name": "Enrollment Management",
            "icon": "",
            "permission": "students.view_enrollment",
            "is_header": True,
            "children": [
                {
                    "name": "Enrollment",
                    "icon": "far fa-user",
                    "url_name": "students:enrollments",
                    "permission": "students.view_enrollment",
                },
            ],
        },
        {
            "name": "MetaData Info",
            "icon": "",
            "permission": "students.view_metadata",
            "is_header": True,
            "children": [
                {
                    "name": "Metadata",
                    "icon": "far fa-user",
                    "url_name": "students:metadata",
                    "permission": "students.view_metadata",
                },
            ],
        },
    ]

    def has_permission_through_groups(user, permission_string):
        """
        Check if user has specific permission through their assigned groups
        """
        if not permission_string:
            return True
        
        # Superuser always has all permissions
        if user.is_superuser:
            return True
        
        
        # Get all user's groups
        user_groups = user.groups.all()
        
        # Check if any of the user's groups has the required permission
        for group in user_groups:
            # Get all permissions for this group
            group_permissions = group.permissions.all()
            
            # Check if the required permission exists in this group
            for perm in group_permissions:
                # Permission format is usually "app_label.permission_codename"
                perm_string = f"{perm.content_type.app_label}.{perm.codename}"
                
                if perm_string == permission_string:
                    return True
        
        return False

    def process_menu_items(menu_config, request):
        """Recursively process menu items based on permissions"""
        accessible_items = []

        for item in menu_config:
           
            
            # Check if user has permission for this item through groups
            if not has_permission_through_groups(user, item.get("permission")):
                continue

            # Create a copy of the item to avoid modifying the original config
            processed_item = item.copy()

            # Process children if they exist
            if "children" in item and item["children"]:
                processed_children = process_menu_items(item["children"], request)
                if processed_children:  # Only add if there are accessible children
                    processed_item["children"] = processed_children
                    processed_item["has_children"] = True

                    # Check if any child is active
                    processed_item["active"] = any(
                        child.get("active", False) for child in processed_children
                    )
                else:
                    continue  # Skip this item if no children are accessible
            else:
                processed_item["has_children"] = False
                # Check if this item is active
                if "url_name" in item:
                    try:
                        resolved_url = reverse(item["url_name"])
                        processed_item["active"] = request.path.startswith(resolved_url)
                    except Exception as e:
                        processed_item["active"] = False

            accessible_items.append(processed_item)

        return accessible_items

    # Process the menu based on group permissions
    sidebar_menu = process_menu_items(SIDEBAR_CONFIG, request)

    return {"sidebar_menu": sidebar_menu}


def get_user_role_display(user):
    """Get user role display name based on groups"""
    if user.is_superuser:
        return "Super Admin"
    elif user.is_staff:
        return "Staff"
    else:
        # Get the first group name as role display, or default to "User"
        user_groups = user.groups.all()
        if user_groups.exists():
            return user_groups.first().name
        return "User"