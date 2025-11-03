(function () {
  var r = document.documentElement;
  var t = localStorage.getItem("theme");
  if (t === "dark") {
    r.classList.add("dark");
    r.classList.remove("watercolor");
  } else if (t === "watercolor") {
    r.classList.add("watercolor");
    r.classList.remove("dark");
  } else if (t === "light") {
    r.classList.remove("dark");
    r.classList.remove("watercolor");
  } else {
    try {
      var m =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (m) {
        r.classList.add("dark");
      }
    } catch (e) {}
  }
  var host = document.querySelector("site-nav");
  if (!host) {
    return;
  }
  var nav = document.createElement("nav");
  nav.className = "nav";
  nav.setAttribute("aria-label", "Primary");
  var links = [
    { href: "index.html", label: "home" },
    { href: "blog.html", label: "blog" },
    { href: "links.html", label: "links" }
  ];
  var path = location.pathname.split("/").pop() || "index.html";
  for (var i = 0; i < links.length; i++) {
    var a = document.createElement("a");
    a.href = links[i].href;
    a.textContent = links[i].label;
    if (links[i].href === path) {
      a.setAttribute("aria-current", "page");
    }
    nav.appendChild(a);
  }

  function currentTheme() {
    if (r.classList.contains("watercolor")) return "watercolor";
    if (r.classList.contains("dark")) return "dark";
    return "light";
  }

  function iconForTheme(theme) {
    if (theme === "dark") return "☀︎";
    if (theme === "watercolor")
      return '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2c-3.5 0-6 2.9-6 6.2 0 3.6 2.5 6.2 5.6 10.2.2.2.6.2.8 0 3.1-4 5.6-6.6 5.6-10.2C18 4.9 15.5 2 12 2z"/></svg>';
    return "☾";
  }

  function setTheme(theme) {
    if (theme === "dark") {
      r.classList.add("dark");
      r.classList.remove("watercolor");
      localStorage.setItem("theme", "dark");
    } else if (theme === "watercolor") {
      r.classList.add("watercolor");
      r.classList.remove("dark");
      localStorage.setItem("theme", "watercolor");
    } else {
      r.classList.remove("dark");
      r.classList.remove("watercolor");
      localStorage.setItem("theme", "light");
    }
    btn.innerHTML = iconForTheme(currentTheme());
    updatePortrait();
  }

  function updatePortrait() {
    var isWc = r.classList.contains("watercolor");
    var imgs = document.querySelectorAll('img[src$="portrait.jpeg"], img[data-original-src="portrait.jpeg"]');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      if (isWc) {
        if (!img.getAttribute("data-original-src")) {
          img.setAttribute("data-original-src", img.getAttribute("src"));
        }
        if (img.getAttribute("src") !== "watercolor.jpeg") {
          img.setAttribute("src", "watercolor.jpeg");
        }
      } else {
        var orig = img.getAttribute("data-original-src") || "portrait.jpeg";
        if (img.getAttribute("src") !== orig) {
          img.setAttribute("src", orig);
        }
      }
    }
  }

  var btn = document.createElement("button");
  btn.className = "theme-toggle";
  btn.id = "theme-toggle";
  btn.setAttribute("aria-label", "Toggle theme");
  btn.innerHTML = iconForTheme(currentTheme());
  btn.addEventListener("click", function () {
    var c = currentTheme();
    var next = c === "light" ? "dark" : c === "dark" ? "watercolor" : "light";
    setTheme(next);
  });
  updatePortrait();
  host.replaceWith(nav, btn);
})();
