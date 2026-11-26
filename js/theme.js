// =========================================
// THEME MANAGEMENT
// =========================================

const themeToggle = document.getElementById("theme-toggle");

// Apply selected theme
function applyTheme(theme) {

    if (theme === "dark") {
        document.body.classList.add("dark-theme");
        themeToggle.checked = true;
    } else {
        document.body.classList.remove("dark-theme");
        themeToggle.checked = false;
    }

    localStorage.setItem("traffic-theme", theme);
}

// Load saved theme
const savedTheme = localStorage.getItem("traffic-theme") || "light";

applyTheme(savedTheme);

// Listen for theme changes
themeToggle.addEventListener("change", function () {

    if (this.checked) {
        applyTheme("dark");
    } else {
        applyTheme("light");
    }

});