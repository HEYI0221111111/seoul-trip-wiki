/* 首爾旅遊攻略：深淺色切換、搜尋、手機選單、目錄高亮。只用原生 JavaScript。 */
(function () {
  "use strict";
  var root = document.body.getAttribute("data-root") || "";
  var docEl = document.documentElement;

  /* ---------- 深淺色模式 ---------- */
  function currentTheme() {
    if (docEl.dataset.theme) return docEl.dataset.theme;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  // 桌機版的主題按鈕放在右上角
  var topBtn = document.querySelector(".topbar .theme-btn");
  if (topBtn) {
    var floatBtn = topBtn.cloneNode(true);
    document.body.appendChild(floatBtn);
  }
  document.querySelectorAll(".theme-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      docEl.dataset.theme = next;
      try { localStorage.setItem("wiki-theme", next); } catch (e) { /* 無法儲存時忽略 */ }
    });
  });

  /* ---------- 手機選單 ---------- */
  var menuBtn = document.querySelector(".menu-btn");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- 搜尋 ---------- */
  var input = document.getElementById("q");
  var box = document.getElementById("results");
  var data = window.WIKI_INDEX || [];
  var active = -1;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function highlight(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (!t) return;
      var re = new RegExp("(" + esc(t).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }
  function snippet(text, term) {
    var i = text.toLowerCase().indexOf(term);
    if (i < 0) return "";
    var s = Math.max(0, i - 24);
    return (s > 0 ? "…" : "") + text.slice(s, i + 56) + "…";
  }
  function search(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    var hits = [];
    data.forEach(function (d) {
      var title = d.t.toLowerCase(), al = d.a.join(" ").toLowerCase(), tg = d.g.join(" ").toLowerCase();
      var sum = d.s.toLowerCase(), body = d.x.toLowerCase();
      var score = 0, ok = terms.every(function (t) {
        var s = 0;
        if (title.indexOf(t) >= 0) s += title === t ? 30 : 12;
        if (al.indexOf(t) >= 0) s += 7;
        if (tg.indexOf(t) >= 0) s += 4;
        if (sum.indexOf(t) >= 0) s += 2;
        if (body.indexOf(t) >= 0) s += 1;
        score += s;
        return s > 0;
      });
      if (ok) hits.push({ d: d, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    return hits.slice(0, 10).map(function (h) {
      var t = terms[0];
      var snip = h.d.t.toLowerCase().indexOf(t) >= 0 ? h.d.s : (snippet(h.d.s, t) || snippet(h.d.x, t) || h.d.s);
      return { d: h.d, snip: snip, terms: terms };
    });
  }
  function show(list, q) {
    active = -1;
    if (!q.trim()) { box.hidden = true; box.innerHTML = ""; return; }
    if (!list.length) {
      box.innerHTML = '<li class="empty">找不到「' + esc(q) + '」</li>';
    } else {
      box.innerHTML = list.map(function (r) {
        return '<li><a href="' + esc(root + encodeURI(r.d.u)) + '">' + highlight(r.d.t, r.terms) +
          '<span class="r-cat">' + esc(r.d.c) + '</span>' +
          '<span class="r-snip">' + highlight(r.snip.slice(0, 90), r.terms) + "</span></a></li>";
      }).join("");
    }
    box.hidden = false;
  }
  function move(step) {
    var links = box.querySelectorAll("a");
    if (!links.length) return;
    active = (active + step + links.length) % links.length;
    links.forEach(function (a, i) { a.classList.toggle("active", i === active); });
    links[active].scrollIntoView({ block: "nearest" });
  }
  if (input && box) {
    input.addEventListener("input", function () { show(search(input.value), input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        var links = box.querySelectorAll("a");
        if (links.length) { e.preventDefault(); links[Math.max(active, 0)].click(); }
      } else if (e.key === "Escape") { input.value = ""; show([], ""); input.blur(); }
    });
    document.addEventListener("keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      if (e.key === "/" && tag !== "input" && tag !== "textarea") {
        e.preventDefault();
        if (window.innerWidth <= 760) document.body.classList.add("nav-open");
        input.focus();
      }
    });
  }

  /* ---------- 目錄高亮 ---------- */
  var tocLinks = document.querySelectorAll(".toc a");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && map[en.target.id]) {
          tocLinks.forEach(function (a) { a.classList.remove("on"); });
          map[en.target.id].classList.add("on");
        }
      });
    }, { rootMargin: "0px 0px -70% 0px" });
    Object.keys(map).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) obs.observe(el);
    });
  }
})();
