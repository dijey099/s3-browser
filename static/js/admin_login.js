document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("admin-login-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const errorMessage = document.getElementById("error-message");
        const loginBtn = document.getElementById("login-btn");

        try {
            loginBtn.textContent = "...";
            loginBtn.disabled = true;

            const response = await fetch("http://localhost:4444/api/admin/auth", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Login failed");
            }

            window.location.href = "/admin/users";
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            loginBtn.textContent = "Go";
            loginBtn.disabled = false;

            console.error("Error:", error);
        }
    });
});

