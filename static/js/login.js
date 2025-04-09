document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("login-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const access_code = document.getElementById("access_code").value;
        const errorMessage = document.getElementById("error-message");
        const loginBtn = document.getElementById("login-btn");

        try {
            loginBtn.textContent = "...";
            loginBtn.disabled = true;

            const response = await fetch("http://localhost:4444/api/auth", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ access_code: access_code })
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Login failed");
            }

            window.location.href = "/home";
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            loginBtn.textContent = "Go";
            loginBtn.disabled = false;

            console.error("Error:", error);
        }
    });
});

