document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("registration-form").addEventListener("submit", async function(event) {
        event.preventDefault();

        const m_name = document.getElementById("name").value;
        const m_role = document.getElementById("role").value;
        const m_mail = document.getElementById("mail").value;
        const m_phone = document.getElementById("phone").value;
        const errorMessage = document.getElementById("error-message");
        const registerBtn = document.getElementById("register-btn");

        try {
            registerBtn.textContent = "...";
            registerBtn.disabled = true;

            const response = await fetch("http://localhost:4444/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: m_name,
                    role: m_role,
                    mail: m_mail,
                    phone: m_phone
                })
            });

            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || "Registration failed");
            }

            window.location.href = "/login";
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            registerBtn.disabled = false;
            registerBtn.textContent = "Request";

            console.error("Error:", error);
        }
    });
});
