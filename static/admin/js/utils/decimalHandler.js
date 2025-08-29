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

export { handleDecimal };