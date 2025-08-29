import { DELETE_CONFIG } from '../config/deleteConfig.js';
import { getCSRFToken } from '../utils/csrf.js';

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
        console.error(`Error deleting ${modelType}:`, error);
        return {
            success: false,
            message: config.errorMessage
        };
    }
}

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

export { confirmDelete, deleteInstance };