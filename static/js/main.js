// File: fastcars-admin/static/js/main.js
document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const navToggle = document.querySelector("[data-nav-toggle]");
    const navBackdrop = document.querySelector("[data-nav-backdrop]");

    const closeNavigation = () => {
        body.classList.remove("nav-open");
        if (navToggle) {
            navToggle.setAttribute("aria-expanded", "false");
        }
        if (navBackdrop) {
            navBackdrop.hidden = true;
        }
    };

    const openNavigation = () => {
        body.classList.add("nav-open");
        if (navToggle) {
            navToggle.setAttribute("aria-expanded", "true");
        }
        if (navBackdrop) {
            navBackdrop.hidden = false;
        }
    };

    if (navToggle) {
        navToggle.addEventListener("click", () => {
            if (body.classList.contains("nav-open")) {
                closeNavigation();
                return;
            }
            openNavigation();
        });
    }

    if (navBackdrop) {
        navBackdrop.addEventListener("click", closeNavigation);
    }

    window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeNavigation();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 920) {
            closeNavigation();
        }
    });

    const closeButtons = document.querySelectorAll("[data-dismiss-flash]");
    closeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const flash = button.closest("[data-flash-message]");
            if (flash) {
                flash.remove();
            }
        });
    });

    const flashes = document.querySelectorAll("[data-flash-message]");
    flashes.forEach((flash) => {
        window.setTimeout(() => {
            if (flash.isConnected) {
                flash.remove();
            }
        }, 5000);
    });

    const confirmForms = document.querySelectorAll("form[data-confirm]");
    confirmForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.getAttribute("data-confirm") || "Are you sure?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    const fileInputs = document.querySelectorAll("[data-file-input]");
    fileInputs.forEach((input) => {
        input.addEventListener("change", () => {
            const feedback = input.parentElement.querySelector(".file-feedback");
            if (!feedback) {
                return;
            }

            const count = input.files ? input.files.length : 0;
            if (!count) {
                feedback.textContent = "No files selected yet.";
                return;
            }

            feedback.textContent = `${count} file${count === 1 ? "" : "s"} selected.`;
        });
    });
});
