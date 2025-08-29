import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

# Configure logger
logger = logging.getLogger('accounts.views')

class LoginView(View):
    """
    Class-based view for handling user authentication with AJAX support
    """

    template_name = "authentication/login.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests - display login form
        """
        try:
            # Redirect authenticated users
            if request.user.is_authenticated:
                logger.info(
                    f"Already authenticated user {request.user.username} attempted to access login page"
                )
                return redirect(self.success_url)

            context = self.get_context_data()
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error in LoginView GET method: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while loading the login page.")
            return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests - process login attempts with AJAX support
        """
        try:
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

            # Extract form data
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()
            remember_me = request.POST.get("remember_me", False)

            # Log login attempt
            logger.info(
                f"Login attempt for username: {username} from IP: {self.get_client_ip(request)}"
            )

            # Validate input data
            validation_errors = self.validate_login_data(username, password)
            if validation_errors:
                logger.warning(
                    f"Validation failed for username: {username}. Errors: {validation_errors}"
                )

                if is_ajax:
                    return JsonResponse({"success": False, "errors": validation_errors})
                else:
                    for error in validation_errors:
                        messages.error(request, error)
                    return render(request, self.template_name, self.get_context_data())

            # Attempt authentication
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    # Successful login
                    auth_login(request, user)

                    # Handle remember me functionality
                    if remember_me:
                        request.session.set_expiry(timedelta(days=30).total_seconds())
                        logger.info(f"Remember me enabled for user: {username}")
                    else:
                        request.session.set_expiry(
                            0
                        )  # Session expires when browser closes

                    # Log successful login
                    logger.info(
                        f"Successful login for user: {username} from IP: {self.get_client_ip(request)}"
                    )

                    if is_ajax:
                        return JsonResponse(
                            {
                                "success": True,
                                "message": f"Welcome back, {user.get_full_name() or user.username}!",
                                "redirect_url": str(self.success_url),
                            }
                        )
                    else:
                        messages.success(
                            request,
                            f"Welcome back, {user.get_full_name() or user.username}!",
                        )
                        return redirect(self.success_url)

                else:
                    # Account is deactivated
                    error_msg = "Your account has been deactivated. Please contact administrator."
                    logger.warning(
                        f"Login attempt with deactivated account: {username}"
                    )

                    if is_ajax:
                        return JsonResponse({"success": False, "errors": [error_msg]})
                    else:
                        messages.error(request, error_msg)
                        return render(
                            request, self.template_name, self.get_context_data()
                        )

            else:
                # Invalid credentials
                error_msg = "Invalid username or password. Please try again."
                logger.warning(
                    f"Failed login attempt for username: {username} from IP: {self.get_client_ip(request)}"
                )

                if is_ajax:
                    return JsonResponse({"success": False, "errors": [error_msg]})
                else:
                    messages.error(request, error_msg)
                    return render(request, self.template_name, self.get_context_data())

        except ValidationError as e:
            logger.error(f"Validation error in LoginView: {str(e)}", exc_info=True)
            error_msg = "Invalid input data provided."

            if is_ajax:
                return JsonResponse({"success": False, "errors": [error_msg]})
            else:
                messages.error(request, error_msg)
                return render(request, self.template_name, self.get_context_data())

        except Exception as e:
            logger.error(
                f"Unexpected error in LoginView POST method: {str(e)}", exc_info=True
            )
            error_msg = "An unexpected error occurred. Please try again later."

            if is_ajax:
                return JsonResponse(
                    {"success": False, "errors": [error_msg]}, status=500
                )
            else:
                messages.error(request, error_msg)
                return render(request, self.template_name, self.get_context_data())

    def validate_login_data(self, username, password):
        """
        Validate login form data
        """
        errors = []

        if not username:
            errors.append("Username is required.")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        elif len(username) > 150:
            errors.append("Username must be less than 150 characters.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 1:
            errors.append("Password must be at least 3 characters long.")

        # Check for suspicious patterns
        if username and self.is_suspicious_username(username):
            errors.append("Invalid username format.")

        return errors

    def is_suspicious_username(self, username):
        """
        Check for suspicious username patterns
        """
        suspicious_patterns = [
            "<",
            ">",
            "script",
            "javascript:",
            "vbscript:",
            "onload=",
        ]
        return any(pattern in username.lower() for pattern in suspicious_patterns)

    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "Unknown")
        return ip

    def get_context_data(self, **kwargs):
        """
        Get context data for template rendering
        """
        context = {
            "title": "Login - Student Management System",
            "login_attempts_exceeded": False,
        }
        context.update(kwargs)
        return context


class LogoutView(View):
    """
    Class-based view for handling user logout
    """

    def post(self, request, *args, **kwargs):
        """
        Handle logout request
        """
        try:
            if request.user.is_authenticated:
                username = request.user.username
                logger.info(
                    f"User {username} logged out from IP: {self.get_client_ip(request)}"
                )

                # Perform logout
                from django.contrib.auth import logout

                logout(request)

                is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

                if is_ajax:
                    return JsonResponse(
                        {
                            "success": True,
                            "message": "You have been successfully logged out.",
                            "redirect_url": reverse_lazy("login"),
                        }
                    )
                else:
                    messages.success(request, "You have been successfully logged out.")
                    return redirect("accounts:login")
            else:
                return redirect("accounts:login")

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
            return redirect("login")

    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "Unknown")
        return ip

