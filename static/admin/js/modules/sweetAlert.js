function confirmSave(event, title) {
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

export { confirmSave };