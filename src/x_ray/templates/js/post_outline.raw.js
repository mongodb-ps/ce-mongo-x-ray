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

collapse.addEventListener("click", (event) => {
    event.preventDefault();
    outline.style.display = "none";
    document.body.style.margin = "0 auto";
    expand.style.display = "inline";
    window.dispatchEvent(new Event("resize"));
});

expand.addEventListener("click", (event) => {
    event.preventDefault();
    outline.style.display = "block";
    document.body.style.margin = "0 auto 0 300px";
    expand.style.display = "none";
    window.dispatchEvent(new Event("resize"));
});

window.addEventListener("scroll", highlightOutline, { passive: true });
highlightOutline();
