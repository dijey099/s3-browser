document.addEventListener("DOMContentLoaded", function () {
    // Send new folder request
    document.getElementById("new-folder").addEventListener("submit", async function(event) {
        event.preventDefault();

        const folderName = document.getElementById("folder-name");
        const path = document.getElementById("object-path");
        const errorMessage = document.getElementById("new-folder-message");
        const createBtn = document.getElementById("new-folder-btn");

        try {
            createBtn.textContent = "...";
            createBtn.disabled = true;

            const response = await fetch("http://localhost:4444/api/folder/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    folder: folderName.value,
                    path: path.value
                })
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Creation failed");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            createBtn.textContent = "Create folder";
            createBtn.disabled = false;
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            createBtn.textContent = "Create folder";
            createBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    // Send upload file request
    document.getElementById("file-upload").addEventListener("submit", async function(event) {
        event.preventDefault();

        const fileInput = document.getElementById("object-file");
        const pathInput = document.getElementById("object-path");
        const errorMessage = document.getElementById("upload-response-message");
        const uploadBtn = document.getElementById("file-upload-btn");

        if (!fileInput.files.length) {
            errorMessage.textContent = "Please select a file.";
            errorMessage.style.display = "block";
            return;
        }

        const fileName = fileInput.files[0].name;
        const filePath = `${pathInput.value}/${fileName}`;

        const uploadForm = new FormData();
        uploadForm.append("file", fileInput.files[0]);

        try {
            errorMessage.textContent = "No file selected.";
            errorMessage.style.display = "none";

            uploadBtn.textContent = "...";
            uploadBtn.disabled = true;

            const response1 = await fetch("http://localhost:4444/api/upload?path=" + filePath, {
                method: "POST"
            });

            const result1 = await response1.json();
            if (!response1.ok) {
                throw new Error(result1.message || "Failed to get presigned URL");
            }

            const response2 = await fetch(result1.url, {
                method: "PUT",
                body: uploadForm
            });

            if (!response2.ok) {
                throw new Error("Failed to upload file");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            uploadBtn.textContent = "Upload file";
            uploadBtn.disabled = false;
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            uploadBtn.textContent = "Upload file";
            uploadBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    // Send delete file request
    document.getElementById("file-delete").addEventListener("submit", async function(event) {
        event.preventDefault();

        const selectedFile = document.getElementById("file-delete-selection");
        const errorMessage = document.getElementById("delete-response-message");
        const deleteBtn = document.getElementById("file-delete-btn");

        if (selectedFile.value == "none") {
            errorMessage.textContent = "Please select a file.";
            errorMessage.style.display = "block";
            return;
        }

        const formData = new FormData();
        formData.append("path", selectedFile.value);

        try {
            deleteBtn.textContent = "...";
            deleteBtn.disabled = true;

            errorMessage.textContent = "No file selected.";
            errorMessage.style.display = "none";

            const response = await fetch("http://localhost:4444/api/delete", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Delete failed");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            const optionToRemove = selectedFile.querySelector(`option[value="${selectedFile.value}"]`);
            if (optionToRemove) {
                optionToRemove.remove();
            }

            selectedFile.value = "none";

            deleteBtn.textContent = "Delete file";
            deleteBtn.disabled = false;
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            deleteBtn.textContent = "Delete file";
            deleteBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    // Handle home button click: return to list buckets
    document.getElementById("home-btn").addEventListener("click", () => {
        window.location = "/home"
    });

    // Handle new folder button: open new-folder Form
    document.getElementById("folder-btn").addEventListener("click", () => {
        document.getElementById("new-folder").style.display = "block";
    });

    // Handle add button: open upload Form
    document.getElementById("add-btn").addEventListener("click", () => {
        document.getElementById("file-upload").style.display = "block";
    });

    // Handle delete button: open delete Form
    document.getElementById("delete-btn").addEventListener("click", () => {
        document.getElementById("file-delete").style.display = "block";
    });

    // Handle close folder Form button: close new-folder Form
    document.getElementById("close-folder-btn").addEventListener("click", () => {
        const errorMessage = document.getElementById("new-folder-message");
        const newFolderForm = document.getElementById("new-folder");

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        newFolderForm.style.display = "none";
    });

    // Handle close upload Form button: close upload Form
    document.getElementById("close-upload-btn").addEventListener("click", () => {
        const errorMessage = document.getElementById("upload-response-message");
        const fileUploadForm = document.getElementById("file-upload");

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        fileUploadForm.style.display = "none";
    });

    // Handle close delete Form button: close delete Form
    document.getElementById("close-delete-btn").addEventListener("click", () => {
        const errorMessage = document.getElementById("delete-response-message");
        const fileDeleteForm = document.getElementById("file-delete");

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        fileDeleteForm.style.display = "none";
    });

    // Handle file browsing: change file name
    document.getElementById("object-file").addEventListener("change", function() {
        let fileName = this.files.length ? this.files[0].name : "No file selected";
        document.getElementById("file-name").textContent = fileName;
    });

});