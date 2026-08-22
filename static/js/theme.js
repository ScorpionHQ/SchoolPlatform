(function () {

    var STORAGE_KEY = "theme";
    var mql = window.matchMedia("(prefers-color-scheme: dark)");

    function current() {

        var saved = localStorage.getItem(STORAGE_KEY);

        if (saved === "dark" || saved === "light") return saved;

        return mql.matches ? "dark" : "light";

    }

    function apply(theme) {

        document.documentElement.setAttribute("data-theme", theme);
        document.documentElement.setAttribute("data-bs-theme", theme);

        var meta = document.querySelector('meta[name="theme-color"]');

        if (meta) meta.setAttribute("content", theme === "dark" ? "#0F172A" : "#6C5CE7");

        document.querySelectorAll(".theme-toggle, .topbar-theme").forEach(function (btn) {

            var icon = btn.querySelector(".theme-icon, .topbar-theme-icon");

            if (!icon) return;

            var dark = theme === "dark";

            icon.classList.toggle("bi-moon-stars-fill", !dark);
            icon.classList.toggle("bi-sun-fill", dark);

            btn.setAttribute("aria-label", dark ? "التبديل إلى الوضع الفاتح" : "التبديل إلى الوضع الداكن");

        });

    }

    function toggle() {

        var next = current() === "dark" ? "light" : "dark";

        localStorage.setItem(STORAGE_KEY, next);

        apply(next);

    }

    document.addEventListener("click", function (e) {

        var btn = e.target.closest(".theme-toggle, .topbar-theme");

        if (btn) {

            e.preventDefault();

            toggle();

        }

    });

    mql.addEventListener("change", function () {

        if (!localStorage.getItem(STORAGE_KEY)) {

            apply(mql.matches ? "dark" : "light");

        }

    });

    apply(current());

})();
