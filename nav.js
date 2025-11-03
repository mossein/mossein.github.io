(function () {
  var r = document.documentElement;
  var t = localStorage.getItem("theme");
  if (t === "dark") {
    r.classList.add("dark");
  } else if (t === "light") {
    r.classList.remove("dark");
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
    { href: "index.html", label: "Home" },
    { href: "blog.html", label: "Blog" },
    { href: "links.html", label: "Links" },
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
  var btn = document.createElement("button");
  btn.className = "theme-toggle";
  btn.id = "theme-toggle";
  btn.setAttribute("aria-label", "Toggle dark mode");
  btn.textContent = r.classList.contains("dark") ? "☀︎" : "☾";
  btn.addEventListener("click", function () {
    var d = r.classList.toggle("dark");
    localStorage.setItem("theme", d ? "dark" : "light");
    btn.textContent = d ? "☀︎" : "☾";
  });
  host.replaceWith(nav, btn);
})();
