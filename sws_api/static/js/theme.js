(function () {
    const savedTheme = localStorage.getItem("sws-theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    function updateButton() {
        const button = document.getElementById("themeToggleBtn");
        if (!button) return;

        const theme = document.documentElement.getAttribute("data-theme");

        button.textContent =
            theme === "dark"
                ? "☀️ Jasny"
                : "🌙 Ciemny";
    }

    window.toggleSwsTheme = function () {
        const current =
            document.documentElement.getAttribute("data-theme") || "light";

        const next = current === "dark" ? "light" : "dark";

        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("sws-theme", next);

        updateButton();
    };

    document.addEventListener("DOMContentLoaded", updateButton);
})();
