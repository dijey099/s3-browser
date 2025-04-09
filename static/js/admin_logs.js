document.addEventListener("DOMContentLoaded", function () {
    const userItems = document.getElementsByClassName("user-item");
    const userBox = document.getElementById("user-info");
    const userName = document.getElementById("user-name");
    const userRole = document.getElementById("user-role");
    const userMail = document.getElementById("user-mail");
    const userPhone = document.getElementById("user-phone");

    Array.from(userItems).forEach(function (item) {
        item.addEventListener("click", async function (event) {
            event.stopPropagation();
            const selectedUser = event.target.textContent || event.target.innerText;

            try {

                const response = await fetch("http://localhost:4444/api/user/info?access_code=" + selectedUser, {
                    method: "GET"
                });

                const result = await response.json();
                if (!response.ok) {
                    const result = await response.json();
                    throw new Error(result.message || "Unknown error");
                }

                userInfo = result.message;
                userName.innerText = userInfo.name;
                userRole.innerText = userInfo.role;
                userMail.innerText = userInfo.mail;
                userPhone.innerText = userInfo.phone;
                userBox.style.display = "block";

            } catch (error) {
                console.error("Error:", error);
            }
        });
    });

    document.getElementById("close-user-info-btn").addEventListener("click", () => {
        userBox.style.display = "none";
    });
});

