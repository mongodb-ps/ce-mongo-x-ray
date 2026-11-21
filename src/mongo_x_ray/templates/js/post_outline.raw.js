const outline = document.getElementById("outline");
const collapse = document.getElementById("collapse-outline");
const expand = document.getElementById("expand-outline");
const headings = Array.from(document.querySelectorAll("h2, h3"));
const links = [];
const list = document.createElement("ul");

headings.forEach((heading) => {
    const item = document.createElement("li");
    const link = document.createElement("a");
    item.classList.add(`outline-${heading.tagName.toLowerCase()}`);
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent;
    item.appendChild(link);
    list.appendChild(item);
    links.push(link);
});
outline.appendChild(list);

function highlightOutline() {
    let current = 0;
    headings.forEach((heading, index) => {
        if (heading.getBoundingClientRect().top <= 80) {
            current = index;
        }
    });
    links.forEach((link, index) => link.classList.toggle("in-view", index === current));
}

// The CSS owns the layout of both report templates, so collapsing only flips a
// class on the body (`body.outline-collapsed` in shared.css) instead of writing
// margins here.
collapse.addEventListener("click", (event) => {
    event.preventDefault();
    document.body.classList.add("outline-collapsed");
    outline.style.display = "none";
    expand.style.display = "inline-flex";
    window.dispatchEvent(new Event("resize"));
});

expand.addEventListener("click", (event) => {
    event.preventDefault();
    document.body.classList.remove("outline-collapsed");
    outline.style.display = "block";
    expand.style.display = "none";
    window.dispatchEvent(new Event("resize"));
});

window.addEventListener("scroll", highlightOutline, { passive: true });
highlightOutline();
