/* LeafyGreen-style tabs for the MongoDB report theme (issue #372).
 *
 * The report is one long page, so the tabs are a section switcher: one tab per
 * top-level (`h2`) section, sticky above the content, with the active tab
 * following the scroll position - the look of
 * https://www.mongodb.design/component/tabs/live-example (44px tall, 4px
 * indicator, green active state).
 *
 * Only the `mongodb.html` templates render this; the default template has no
 * `mongodb-report` class on the body, so the script does nothing there.
 */
(function () {
    if (!document.body.classList.contains("mongodb-report")) return;

    var headings = Array.prototype.slice.call(document.querySelectorAll(".markdown-body > h2"));
    if (headings.length < 2) return;

    var bar = document.createElement("nav");
    bar.className = "report-tabs";
    bar.setAttribute("aria-label", "Report sections");

    var tabs = headings.map(function (heading) {
        var tab = document.createElement("a");
        tab.className = "report-tab";
        tab.href = "#" + heading.id;
        tab.textContent = heading.textContent.trim();
        tab.addEventListener("click", function (event) {
            event.preventDefault();
            heading.scrollIntoView({ behavior: "smooth", block: "start" });
            if (window.history && window.history.replaceState) {
                window.history.replaceState(null, "", "#" + heading.id);
            }
        });
        bar.appendChild(tab);
        return tab;
    });

    var header = document.querySelector(".mongo-header");
    if (header && header.parentNode) {
        header.parentNode.insertBefore(bar, header.nextSibling);
    } else {
        document.body.insertBefore(bar, document.body.firstChild);
    }

    function highlight() {
        var current = 0;
        headings.forEach(function (heading, index) {
            if (heading.getBoundingClientRect().top <= 120) current = index;
        });
        tabs.forEach(function (tab, index) {
            tab.classList.toggle("is-active", index === current);
            if (index === current) tab.setAttribute("aria-current", "true");
            else tab.removeAttribute("aria-current");
        });
        // keep the active tab in view when the bar scrolls horizontally
        var active = tabs[current];
        if (active && bar.scrollWidth > bar.clientWidth) {
            var left = active.offsetLeft;
            var right = left + active.offsetWidth;
            if (left < bar.scrollLeft) {
                bar.scrollLeft = left - 16;
            } else if (right > bar.scrollLeft + bar.clientWidth) {
                bar.scrollLeft = right - bar.clientWidth + 16;
            }
        }
    }

    window.addEventListener("scroll", highlight, { passive: true });
    highlight();
})();
