AOS.init({
    duration: 600,
    easing: "ease-out-cubic",
    once: true,
    offset: 60,
    disableMutationObserver: true,
});

document.querySelectorAll(".toggle-password").forEach(function(btn) {
    btn.addEventListener("click", function() {
        var group = this.closest(".input-group");
        if (!group) return;
        var input = group.querySelector("input");
        if (!input) return;
        var icon = this.querySelector("i");
        if (input.type === "password") {
            input.type = "text";
            icon.classList.replace("bi-eye", "bi-eye-slash");
            this.setAttribute("aria-label", "Hide password");
        } else {
            input.type = "password";
            icon.classList.replace("bi-eye-slash", "bi-eye");
            this.setAttribute("aria-label", "Show password");
        }
    });
});
