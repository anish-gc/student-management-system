// Configuration for different model types
const DELETE_CONFIG = {
    'staff': {
        urlTemplate: '/staffs/staff-delete/{id}/',
        successMessage: '{name} has been deleted successfully!',
        errorMessage: 'Failed to delete user. Please try again.'
    },
    'group': {
        urlTemplate: '/dashboard/groups/delete/{id}/',
        successMessage: 'Group "{name}" has been deleted successfully!',
        errorMessage: 'Failed to delete group. Please try again.'
    },
    'banner': {
        urlTemplate: '/dashboard/banners/delete/{id}/',
        successMessage: 'Banner "{name}" has been deleted successfully!',
        errorMessage: 'Failed to delete banner. Please try again.'
    },
    'default': {
        urlTemplate: '/dashboard/{model}/delete/{id}/',
        successMessage: 'Item has been deleted successfully!',
        errorMessage: 'Failed to delete item. Please try again.'
    }
};

export { DELETE_CONFIG };