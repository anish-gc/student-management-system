// Configuration for toggle actions
const TOGGLE_CONFIG = {
   
    staff: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },
    student: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },


    instructor: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },
    course: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/api/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },
    enrollment: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },
    metadata: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: '{name} status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    },
    default: {
        urlTemplate: '/toggle/{model}/{id}/',
        fieldUrlTemplate: '/toggle/{model}/{id}/{field}/',
        successMessage: 'Status has been updated successfully!',
        errorMessage: 'Failed to update status. Please try again.',
        activeText: 'activate',
        inactiveText: 'deactivate'
    }
};

/**
 * Confirm toggle action with SweetAlert
 * @param {Event} event - The click event
 * @param {string} modelType - The type of model (user, group, etc.)
 * @param {string} instanceId - The instance ID
 * @param {string} instanceName - The instance name for display
 * @param {boolean} currentStatus - Current active status (true for active, false for inactive)
 * @param {string} fieldName - The field name to toggle (default: 'is_active')
 * @param {Object} customConfig - Optional custom configuration
 */
function confirmToggle(event, modelType, instanceId, instanceName, currentStatus, fieldName = 'is_active', customConfig = null) {
    event.preventDefault();

    // Get configuration for this model type
    const config = customConfig || TOGGLE_CONFIG[modelType] || TOGGLE_CONFIG.default;

    // Determine action text based on current status
    const actionText = currentStatus ? config.inactiveText : config.activeText;
    const newStatus = currentStatus ? 'inactive' : 'active';

    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to ${actionText} ${instanceName}. Do you want to continue?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: currentStatus ? '#dc3545' : '#28a745', // Red for deactivate, green for activate
        cancelButtonColor: '#6c757d',
        confirmButtonText: `Yes, ${actionText} it!`,
        cancelButtonText: 'Cancel',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            return toggleInstance(modelType, instanceId, instanceName, fieldName, config);
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed) {
            const response = result.value;
            if (response && response.success) {
                Swal.fire({
                    title: 'Updated!',
                    text: response.message || config.successMessage.replace('{name}', instanceName),
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    // Update the status badge in the UI
                    updateStatusBadge(instanceId, response[fieldName] || response.is_active, modelType, fieldName);

                    // Optional: Redirect if specified in response
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    }
                });
            } else {
                Swal.fire({
                    title: 'Error!',
                    text: response.message || config.errorMessage,
                    icon: 'error'
                });
            }
        }
    });
}

/**
 * Toggle instance status via AJAX
 * @param {string} modelType - The type of model
 * @param {string} instanceId - The instance ID
 * @param {string} instanceName - The instance name
 * @param {string} fieldName - The field name to toggle
 * @param {Object} config - Configuration object
 */
async function toggleInstance(modelType, instanceId, instanceName, fieldName, config) {
    try {
        // Build the URL - use field-specific URL if field is not 'is_active'
        let toggleUrl;
        if (fieldName === 'is_active') {
            toggleUrl = config.urlTemplate
                .replace('{model}', modelType)
                .replace('{id}', instanceId);
        } else {
            toggleUrl = config.fieldUrlTemplate
                .replace('{model}', modelType)
                .replace('{id}', instanceId)
                .replace('{field}', fieldName);
        }
        const response = await fetch(toggleUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                'csrfmiddlewaretoken': getCSRFToken()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        return {
            success: false,
            message: config.errorMessage
        };
    }
}

/**
 * Update the status badge in the UI after successful toggle
 * @param {string} instanceId - The instance ID
 * @param {boolean} newValue - New field value
 * @param {string} modelType - The model type
 * @param {string} fieldName - The field name that was toggled
 */
function updateStatusBadge(instanceId, newValue, modelType = 'user', fieldName = 'is_active') {
    // Find the status cell for this instance
    const statusCell = document.querySelector(`[data-${modelType}-id="${instanceId}"] .status-cell`);

    if (statusCell) {
        const badge = statusCell.querySelector('.badge');
        const icon = badge.querySelector('i');
        const toggleLink = statusCell.querySelector('a');

        if (fieldName === 'is_active') {
            if (newValue) {
                // Update to active state
                badge.className = 'badge badge-success';
                icon.className = 'fa fa-check';
                badge.innerHTML = '<i class="fa fa-check"></i> Active';

                // Update toggle link
                if (toggleLink) {
                    toggleLink.className = 'text-danger';
                    toggleLink.innerHTML = '<i class="fa fa-toggle-off"></i> Deactivate';
                    toggleLink.onclick = function (e) {
                        confirmToggle(e, modelType, instanceId, 'Item', true, fieldName);
                    };
                }
            } else {
                // Update to inactive state
                badge.className = 'badge badge-danger';
                icon.className = 'fa fa-times';
                badge.innerHTML = '<i class="fa fa-times"></i> Inactive';

                // Update toggle link
                if (toggleLink) {
                    toggleLink.className = 'text-success';
                    toggleLink.innerHTML = '<i class="fa fa-toggle-on"></i> Activate';
                    toggleLink.onclick = function (e) {
                        confirmToggle(e, modelType, instanceId, 'Item', false, fieldName);
                    };
                }
            }
        } else {
            // Handle other boolean fields generically
            const fieldDisplay = fieldName.replace('is_', '').replace('_', ' ');
            if (newValue) {
                badge.className = 'badge badge-success';
                badge.innerHTML = `<i class="fa fa-check"></i> ${fieldDisplay}`;
            } else {
                badge.className = 'badge badge-secondary';
                badge.innerHTML = `<i class="fa fa-times"></i> Not ${fieldDisplay}`;
            }
        }
    }
}








// Configuration for different model types
const DELETE_CONFIG = {
    'group': {
        urlTemplate: '/groups/{id}/delete/',
        successMessage: 'Group "{name}" has been deleted successfully!',
        errorMessage: 'Failed to delete group. Please try again.'
    },
    'staff': {
        urlTemplate: '/staffs/{id}/delete/',
        successMessage: '{name} has been deleted successfully!',
        errorMessage: 'Failed to delete user. Please try again.'
    },
    'student': {
        urlTemplate: '/students/{id}/delete/',
        successMessage: '{name} has been deleted successfully!',
        errorMessage: 'Failed to delete student. Please try again.'
    },
    'instructor': {
        urlTemplate: '/instructors/{id}/delete/',
        successMessage: 'Banner "{name}" has been deleted successfully!',
        errorMessage: 'Failed to delete instructor. Please try again.'
    },
    'course': {
        urlTemplate: '/courses/{id}/delete/',
        successMessage: 'Item has been deleted successfully!',
        errorMessage: 'Failed to delete course. Please try again.'
    },
    'enrollment': {
        urlTemplate: '/enrollments/{id}/delete/',
        successMessage: 'Item has been deleted successfully!',
        errorMessage: 'Failed to delete enrollment. Please try again.'
    },
    'metadata': {
        urlTemplate: '/metadata/{id}/delete/',
        successMessage: '{name} has been deleted successfully!',
        errorMessage: 'Failed to delete metadata. Please try again.'
    },


};

/**
 * Confirm delete action with SweetAlert
 * @param {Event} event - The click event
 * @param {string} modelType - The type of model (user, group, banner, etc.)
 * @param {string} instanceId - The instance ID
 * @param {string} instanceName - The instance name for display
 * @param {Object} customConfig - Optional custom configuration
 */
function confirmDelete(event, modelType, instanceId, instanceName, customConfig = null) {
    event.preventDefault();

    // Get configuration for this model type
    const config = customConfig || DELETE_CONFIG[modelType] || DELETE_CONFIG.default;

    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete ${instanceName}. This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        showLoaderOnConfirm: true,
        preConfirm: () => {
            return deleteInstance(modelType, instanceId, instanceName, config);
        },
        allowOutsideClick: () => !Swal.isLoading()
    }).then((result) => {
        if (result.isConfirmed) {
            const response = result.value;
            if (response && response.success) {
                Swal.fire({
                    title: 'Deleted!',
                    text: response.message || config.successMessage.replace('{name}', instanceName),
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    // Optional: Remove the row from table or redirect
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    } else {
                        const row = document.querySelector(`[data-${modelType}-id="${instanceId}"]`);
                        if (row) {
                            row.remove();
                        }
                    }
                });
            } else {
                Swal.fire({
                    title: 'Error!',
                    text: response.message || config.errorMessage,
                    icon: 'error'
                });
            }
        }
    });
}

/**
 * Delete instance via AJAX
 * @param {string} modelType - The type of model
 * @param {string} instanceId - The instance ID
 * @param {string} instanceName - The instance name
 * @param {Object} config - Configuration object
 */
async function deleteInstance(modelType, instanceId, instanceName, config) {
    try {
        // Build the URL
        let deleteUrl = config.urlTemplate
            .replace('{model}', modelType)
            .replace('{id}', instanceId);

        const response = await fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                'csrfmiddlewaretoken': getCSRFToken()
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;

    } catch (error) {
        return {
            success: false,
            message: config.errorMessage
        };
    }
}

/**
 * Get CSRF token from cookie
 */
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}
function confirmSave(event, title) {
    // const pathname = event.target.href ?? event.target.parentElement.href
    const form = document.querySelector("form");

    event.preventDefault();

    Swal.fire({
        title: title ?? "Do you want to save the changes?",
        showDenyButton: true,
        showCancelButton: true,
        confirmButtonText: title ? "Yes" : "Save",
        denyButtonText: title ? "No" : `Don't save`,
    }).then((result) => {
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
            Swal.fire("Changes is saved", "", "success");
        } else if (result.isDenied) {
            Swal.fire("Changes is not saved", "", "info");
        }
    });
}
/**
 * Enhanced global form validation with better error handling and user experience
 * @param {string} formSelector - jQuery selector for the form
 * @param {Object} rules - Validation rules object
 * @param {Object} messages - Custom error messages (optional)
 */
function globalFormValidation(formSelector, rules, messages = {}) {
    // Ensure jQuery validate is available
    if (!$.fn.validate) {
        console.error('jQuery Validate plugin is required');
        return;
    }

    const defaultMessages = {
        required: "This field is required",
        email: "Please enter a valid email address",
        minlength: "Please enter at least {0} characters",
        maxlength: "Please enter no more than {0} characters",
        digits: "Please enter only digits",
        ...messages
    };

    $(formSelector).validate({
        rules: rules,
        messages: defaultMessages,

        errorElement: 'div',
        errorClass: 'invalid-feedback',

        errorPlacement: function (error, element) {
            // Handle Select2 elements
            if (element.hasClass('select2bs4')) {
                error.insertAfter(element.next('.select2-container'));
            }
            // Handle checkbox elements
            else if (element.attr('type') === 'checkbox') {
                error.insertAfter(element.closest('.form-check'));
            }
            // Default placement
            else {
                error.insertAfter(element);
            }
        },

        highlight: function (element, errorClass, validClass) {
            const $element = $(element);

            // Handle Select2 elements
            if ($element.hasClass('select2bs4')) {
                $element.next('.select2-container')
                    .find('.select2-selection')
                    .addClass('is-invalid');
            } else {
                $element.addClass('is-invalid').removeClass('is-valid');
            }
        },

        unhighlight: function (element, errorClass, validClass) {
            const $element = $(element);

            // Handle Select2 elements
            if ($element.hasClass('select2bs4')) {
                $element.next('.select2-container')
                    .find('.select2-selection')
                    .removeClass('is-invalid')
                    .addClass('is-valid');
            } else {
                $element.removeClass('is-invalid').addClass('is-valid');
            }
        },

        invalidHandler: function (event, validator) {
            // FIXED: Check if we already showed the error to prevent duplicates
            if (validator.numberOfInvalids() > 0 && !validator.errorShown) {
                validator.errorShown = true;

                // Show toast notification
                if (typeof toastr !== 'undefined') {
                    toastr.error(`Please correct ${validator.numberOfInvalids()} field(s) to continue.`);
                }

                // Focus on first invalid field
                const firstError = validator.errorList[0];
                if (firstError) {
                    const $element = $(firstError.element);

                    // Handle Select2 focus
                    if ($element.hasClass('select2bs4')) {
                        $element.select2('open');
                    } else {
                        $element.focus();
                    }

                    // Scroll to first error
                    $('html, body').animate({
                        scrollTop: $element.offset().top - 100
                    }, 500);
                }

                // Reset the flag after a short delay
                setTimeout(function () {
                    validator.errorShown = false;
                }, 1000);
            }
        },

        submitHandler: function (form) {
            // This will be called when form is valid
            return true;
        }
    });
}

/**
 * Enhanced AJAX request handler for Django forms with improved error handling and UX
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {string} formId - Form element ID
 * @param {FormData} formData - Form data to send
 * @param {string} sendUrl - URL to send the request to
 * @param {string} redirectUrl - URL to redirect after success
 * @param {Object} options - Additional options
 */
function handleAjaxRequestForDjangoForm(method, formId, formData, sendUrl, redirectUrl, options = {}) {
    // Default options
    const defaultOptions = {
        showSuccessToast: true,
        redirectDelay: 1000,
        onSuccess: null,
        onError: null,
        onComplete: null,
        ...options
    };

    const $form = $("#" + formId);
    const $submitButton = $form.find('[type="submit"]');
    const $spinner = $submitButton.find('.spinner-border');
    const $buttonText = $submitButton.find('.btn-text');

    // Get CSRF token
    const token = $form.find("input[name=csrfmiddlewaretoken]").val();

    if (!token) {
        if (typeof toastr !== 'undefined') {
            toastr.error('Security token missing. Please refresh the page.');
        }
        return;
    }

    // Disable submit button and show loading state
    $submitButton.prop('disabled', true);
    $spinner.removeClass('d-none');
    if ($buttonText.length) {
        $buttonText.text('Saving...');
    }

    // Disable form inputs to prevent changes during submission
    $form.find('input, select, textarea').prop('disabled', true);

    $.ajax({
        url: sendUrl,
        type: method,
        headers: {
            "X-CSRFToken": token,
            "X-Requested-With": "XMLHttpRequest"
        },
        data: formData,
        dataType: 'json',
        contentType: false,
        processData: false,
        cache: false,
        timeout: 30000, // 30 seconds timeout

        success: function (response) {
            // Handle success response
            if (defaultOptions.showSuccessToast && typeof toastr !== 'undefined') {
                const message = response.message || response.response || "Operation completed successfully.";
                toastr.success(message);
            }

            // Execute custom success callback
            if (typeof defaultOptions.onSuccess === 'function') {
                defaultOptions.onSuccess(response);
            }

            // Redirect after delay
            if (redirectUrl) {
                setTimeout(function () {
                    window.location.href = redirectUrl;
                }, defaultOptions.redirectDelay);
            }
        },

        error: function (xhr, status, error) {
          

            let errorMessage = "An error occurred. Please try again.";

            try {
                const response = JSON.parse(xhr.responseText);
                // Handle validation errors
                if (response.errors) {
                    handleFormErrors($form, response.errors);
                    errorMessage = "Please correct the errors below.";
                } else if (response.error) {
                    errorMessage = response.error;
                } else if (response.message) {
                    errorMessage = response.message;
                }
            } catch (e) {
                // Handle different HTTP status codes
                switch (xhr.status) {
                    case 400:
                        errorMessage = "Invalid data submitted.";
                        break;
                    case 401:
                        errorMessage = "You are not authorized to perform this action.";
                        break;
                    case 403:
                        errorMessage = "Access denied.";
                        break;
                    case 404:
                        errorMessage = "The requested resource was not found.";
                        break;
                    case 500:
                        errorMessage = "Server error. Please try again later.";
                        break;
                    case 0:
                        errorMessage = "Network error. Please check your connection.";
                        break;
                    default:
                        errorMessage = `Error ${xhr.status}: ${xhr.statusText}`;
                }
            }

            // Show error message
            if (typeof toastr !== 'undefined') {
                toastr.error(errorMessage);
            } else {
                alert(errorMessage);
            }

            // Execute custom error callback
            if (typeof defaultOptions.onError === 'function') {
                defaultOptions.onError(xhr, status, error);
            }
        },

        complete: function (xhr, status) {
            // Re-enable form and button
            $submitButton.prop('disabled', false);
            $spinner.addClass('d-none');
            if ($buttonText.length) {
                $buttonText.text('Save');
            }

            // Re-enable form inputs
            $form.find('input, select, textarea').prop('disabled', false);

            // Execute custom complete callback
            if (typeof defaultOptions.onComplete === 'function') {
                defaultOptions.onComplete(xhr, status);
            }
        }
    });
}

/**
 * Handle form validation errors returned from Django
 * @param {jQuery} $form - Form jQuery object
 * @param {Object} errors - Error object from Django response
 */
function handleFormErrors($form, errors) {
    // Clear existing errors
    $form.find('.is-invalid').removeClass('is-invalid');
    $form.find('.invalid-feedback').remove();

    // Display field errors
    Object.keys(errors).forEach(function (fieldName) {
        const $field = $form.find(`[name="${fieldName}"]`);
        const errorMessages = Array.isArray(errors[fieldName]) ? errors[fieldName] : [errors[fieldName]];

        if ($field.length) {
            $field.addClass('is-invalid');

            const errorHtml = errorMessages.map(msg => `<div class="invalid-feedback d-block">${msg}</div>`).join('');

            // Handle Select2 elements
            if ($field.hasClass('select2bs4')) {
                $field.next('.select2-container').after(errorHtml);
                $field.next('.select2-container').find('.select2-selection').addClass('is-invalid');
            } else {
                $field.after(errorHtml);
            }
        }
    });

    // Focus on first error field
    const $firstError = $form.find('.is-invalid').first();
    if ($firstError.length) {
        if ($firstError.hasClass('select2bs4')) {
            $firstError.select2('open');
        } else {
            $firstError.focus();
        }

        // Scroll to first error
        $('html, body').animate({
            scrollTop: $firstError.offset().top - 100
        }, 500);
    }
}
/**
 * Utility function to handle decimal input restrictions
 * @param {Event} event - Keydown event
 * @param {number} decimalPlaces - Number of decimal places allowed
 */
function handleDecimal(event, decimalPlaces = 2) {
    const key = event.which || event.keyCode;
    const value = event.target.value;

    // Allow backspace, delete, tab, escape, enter
    if ([8, 9, 27, 13, 46].includes(key) ||
        // Allow Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
        (key === 65 && event.ctrlKey) ||
        (key === 67 && event.ctrlKey) ||
        (key === 86 && event.ctrlKey) ||
        (key === 88 && event.ctrlKey) ||
        // Allow home, end, left, right, down, up
        (key >= 35 && key <= 40)) {
        return;
    }

    // Ensure only digits and decimal point
    if ((key < 48 || key > 57) && key !== 190 && key !== 110) {
        event.preventDefault();
        return;
    }

    // Only one decimal point allowed
    if ((key === 190 || key === 110) && value.includes('.')) {
        event.preventDefault();
        return;
    }

    // Check decimal places
    if (value.includes('.')) {
        const parts = value.split('.');
        if (parts[1] && parts[1].length >= decimalPlaces) {
            event.preventDefault();
        }
    }
}
