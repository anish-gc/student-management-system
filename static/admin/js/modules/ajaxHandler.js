import { getCSRFToken } from '../utils/csrf.js';

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
        console.error('CSRF token not found');
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
            console.error("AJAX Error:", {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText,
                error: error
            });

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

export { handleAjaxRequestForDjangoForm, handleFormErrors };