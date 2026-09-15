(function () {
    const theme = localStorage.getItem("sws-theme") || "light";
    document.documentElement.setAttribute("data-theme", theme);
})();

function updateSwsThemeButton() {
    const theme =
        document.documentElement.getAttribute("data-theme");

    const btn =
        document.getElementById("themeToggleBtn");

    if (!btn) return;

    if (theme === "dark") {
        btn.textContent = "☀️ Jasny";
    } else {
        btn.textContent = "🌙 Ciemny";
    }
}

function toggleSwsTheme() {
    const current =
        document.documentElement.getAttribute("data-theme");

    const next =
        current === "dark" ? "light" : "dark";

    document.documentElement.setAttribute(
        "data-theme",
        next
    );

    localStorage.setItem(
        "sws-theme",
        next
    );

    updateSwsThemeButton();
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

document.addEventListener(
    "DOMContentLoaded",
    function () {
        updateSwsThemeButton();
    }
);
