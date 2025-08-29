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

export { globalFormValidation };