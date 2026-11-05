
// TrustVault basic JavaScript

// Ask for confirmation before submitting a delete form.
document.addEventListener("DOMContentLoaded", function () {
    const deleteForms = document.querySelectorAll(".confirm-delete");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmed = confirm(
                "Are you sure you want to delete this document?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});
