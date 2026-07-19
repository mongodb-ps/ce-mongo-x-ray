VIEWPORT_WIDTH = 1200;
linkElms = [];
titleElms = [];
charts = charts || [];

hljs.addPlugin(new CopyButtonPlugin({
    hook: (_, el) => el.textContent
}));

function getWindowHeight() {
    return window.innerHeight ||
        document.documentElement.clientHeight ||
        document.body.clientHeight;
}

function getWindowWidth() {
    return window.innerWidth ||
        document.documentElement.clientWidth ||
        document.body.clientWidth;
}

function highlightOutline() {
    for (var i = 0; i < titleElms.length; i++) {
        var rect = titleElms[i].getBoundingClientRect();
        var top = i == 0 ? 0 : rect.top;
        var bottom = i == titleElms.length - 1 ? document.body.scrollHeight : titleElms[i + 1].getBoundingClientRect().top;
        if (top < 1 && bottom > 1) {
            linkElms[i].classList.add('in-view');
        } else {
            linkElms[i].classList.remove('in-view');
        }
    }
}

function createList(li_elms) {
    var ul = document.createElement('ul');
    for (var i = 0; i < li_elms.length; i++) {
        var li = document.createElement('li');
        var link = document.createElement('a');
        linkElms.push(link);
        link.href = '#' + li_elms[i].id;
        link.textContent = li_elms[i].textContent;
        li.appendChild(link);
        ul.appendChild(li);
    }
    return ul;
}

window.onload = function () {
    var outline = document.getElementById('outline');
    var h2 = document.getElementsByTagName('h2');
    var ul = document.createElement('ul');
    var body = document.getElementsByClassName('markdown-body')[0];
    for (var i = 0; i < h2.length; i++) {
        titleElms.push(h2[i]);
        var li = document.createElement('li');
        var link = document.createElement('a');
        linkElms.push(link);
        link.href = '#' + h2[i].id;
        link.textContent = h2[i].textContent;
        var children = [];
        for (var next = h2[i].nextElementSibling; next && next.tagName !== 'H2'; next = next.nextElementSibling) {
            if (next.tagName === 'H3') {
                children.push(next);
                titleElms.push(next);
            }
        }
        ul.appendChild(li);
        li.appendChild(link);
        li.appendChild(createList(children));
    }
    outline.appendChild(ul);
    var outlineWidth = outline.offsetWidth + 20;
    body.style.margin = '0 auto 0 ' + outlineWidth + 'px';
    var expand = document.getElementById('expand-outline');
    var collapse = document.getElementById('collapse-outline');
    var state = 1;
    var margins = ["0 auto", '0 auto 0 ' + outlineWidth + 'px'];
    window.onresize = function () {
        var blank = (getWindowWidth() - VIEWPORT_WIDTH) / 2;
        if (blank > outlineWidth) {
            margins = ["0 auto", "0 auto"];
        } else {
            margins = ["0 auto", '0 auto 0 ' + outlineWidth + 'px'];
        }
        body.style.margin = margins[state];
        for (var i = 0; i < charts.length; i++) {
            charts[i].resize();
        }
    };
    var click = function () {
        state = state == 0 ? 1 : 0;
        outline.style.display = state ? "block" : "none";
        expand.style.display = state ? "none" : "inline";
        body.style.margin = margins[state];
        window.dispatchEvent(new Event("resize"));
        return false;
    };
    collapse.onclick = click;
    expand.onclick = click;
    highlightOutline();
    window.onscroll = highlightOutline;
    hljs.highlightAll();
};
