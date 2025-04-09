document.addEventListener("DOMContentLoaded", function () {
    const userItems = document.getElementsByClassName("user-item");
    const userBox = document.getElementById("user-info");
    const userName = document.getElementById("user-name");
    const userRole = document.getElementById("user-role");
    const userMail = document.getElementById("user-mail");
    const userPhone = document.getElementById("user-phone");
    const userAC = document.getElementById("access_code");
    const errorMessage = document.getElementById("delete-user-message");
    const deleteBtn = document.getElementById("delete-user-btn");

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
                userAC.value = selectedUser;
                userBox.style.display = "block";

            } catch (error) {
                console.error("Error:", error);
            }
        });
    });

    deleteBtn.addEventListener("click", async function (event) {
        try {
            deleteBtn.textContent = "...";
            deleteBtn.disabled = true;

            access_code = userAC.value;

            const response = await fetch("http://localhost:4444/api/user/delete?access_code=" + access_code, {
                method: "POST"
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || "Unknown error");
            }

            errorMessage.textContent = "Done";
            errorMessage.style.display = "block";

            sleep(1500);
            location.reload();
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = "block";

            deleteBtn.textContent = "Delete";
            deleteBtn.disabled = false;

            console.error("Error:", error);
        }
    });

    document.getElementById("close-user-btn").addEventListener("click", () => {

        if ((errorMessage.textContent == "Done") && (errorMessage.style.display == "block")) {
            location.reload();
            errorMessage.textContent = "";
        }

        errorMessage.style.display = "none";
        userBox.style.display = "none";
    });
});

