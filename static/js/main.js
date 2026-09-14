if (typeof AOS !== 'undefined') {
    AOS.init({
        duration: 600,
        easing: "ease-out-cubic",
        once: true,
        offset: 60,
        disableMutationObserver: true,
    });
}

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

// New-gen toast — robust auto-dismiss (works even if AOS fails)
function initToasts() {
    document.querySelectorAll(".toast-modern").forEach(function(toast) {
        if (toast.dataset.toastInit) return;
        toast.dataset.toastInit = "1";
        var closeBtn = toast.querySelector(".toast-close");
        var timeout;
        function dismiss() {
            toast.style.animation = "toastSlideOut 0.3s ease forwards";
            setTimeout(function() { if (toast.parentNode) toast.remove(); }, 300);
        }
        if (closeBtn) closeBtn.addEventListener("click", function(e) {
            e.preventDefault();
            clearTimeout(timeout);
            dismiss();
        });
        timeout = setTimeout(dismiss, 4000);
        toast.addEventListener("mouseenter", function() {
            clearTimeout(timeout);
            var bar = toast.querySelector(".toast-progress-bar");
            if (bar) bar.style.animationPlayState = "paused";
        });
        toast.addEventListener("mouseleave", function() {
            timeout = setTimeout(dismiss, 1200);
            var bar = toast.querySelector(".toast-progress-bar");
            if (bar) bar.style.animationPlayState = "running";
        });
    });
}
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initToasts);
} else {
    initToasts();
}
