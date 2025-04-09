document.addEventListener("DOMContentLoaded", function () {
    // Send create bucket request
    document.getElementById("new-bucket-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const bucketInput = document.getElementById("new-bucket-name");
        const errorMessage = document.getElementById("new-bucket-message");
        const createBtn = document.getElementById("new-bucket-btn");

        const bucketName = bucketInput.value;

        try {
            errorMessage.textContent = "No bucket name.";
            errorMessage.style.display = "none";

            createBtn.textContent = "...";
            createBtn.disabled = true;

            const response = await fetch("http://localhost:4444/api/bucket/create?name=" + bucketName, {
                method: "POST"
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || "Failed to create bucket");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            createBtn.textContent = "Create";
            createBtn.disabled = false;
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            createBtn.textContent = "Create";
            createBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    // Send delete bucket request
    document.getElementById("delete-bucket-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const selectedBucket = document.getElementById("delete-bucket-selection");
        const errorMessage = document.getElementById("delete-response-message");
        const deleteBtn = document.getElementById("delete-bucket-btn");

        if (selectedBucket.value == "none") {
            errorMessage.textContent = "Please select a bucket.";
            errorMessage.style.display = "block";
            return;
        }

         const bucketName = selectedBucket.value;

        try {
            deleteBtn.textContent = "...";
            deleteBtn.disabled = true;

            errorMessage.textContent = "No bucket selected.";
            errorMessage.style.display = "none";

            const response = await fetch("http://localhost:4444/api/bucket/delete?name=" + bucketName, {
                method: "POST"
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Delete failed");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            const optionToRemove = selectedBucket.querySelector(`option[value="${selectedBucket.value}"]`);
            if (optionToRemove) {
                optionToRemove.remove();
            }

            selectedBucket.value = "none";

            deleteBtn.textContent = "Delete";
            deleteBtn.disabled = false;
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            deleteBtn.textContent = "Delete";
            deleteBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    // Handle home button click for admin: return to list buckets
    document.getElementById("admin-home-btn").addEventListener("click", () => {
        window.location = "/admin/users"
    });

    // Handle add button: open upload Form
    document.getElementById("add-btn").addEventListener("click", () => {
        document.getElementById("new-bucket-form").style.display = "block";
    });

    // Handle delete button: open delete Form
    document.getElementById("delete-btn").addEventListener("click", () => {
        document.getElementById("delete-bucket-form").style.display = "block";
    });

    // Handle close upload Form button: close upload Form
    document.getElementById("close-new-bucket-btn").addEventListener("click", () => {
        const errorMessage = document.getElementById("new-bucket-message");
        const fileUploadForm = document.getElementById("new-bucket-form");

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        fileUploadForm.style.display = "none";
    });

    // Handle close delete Form button: close delete Form
    document.getElementById("close-delete-bucket-btn").addEventListener("click", () => {
        const errorMessage = document.getElementById("delete-response-message");
        const fileDeleteForm = document.getElementById("delete-bucket-form");

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        fileDeleteForm.style.display = "none";
    });
});