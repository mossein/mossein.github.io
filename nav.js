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


  var blob = document.createElement("div");
  blob.className = "cursor-blob";
  document.body.appendChild(blob);
  var blobX = 0, blobY = 0, targetX = 0, targetY = 0;
  document.addEventListener("mousemove", function(e) {
    targetX = e.clientX;
    targetY = e.clientY;
  });
  function animateBlob() {
    blobX += (targetX - blobX) * 0.08;
    blobY += (targetY - blobY) * 0.08;
    blob.style.left = blobX + "px";
    blob.style.top = blobY + "px";
    requestAnimationFrame(animateBlob);
  }
  animateBlob();

  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length > 0 && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });
    reveals.forEach(function(el) { observer.observe(el); });
  }

  var greeting = document.getElementById("greeting");
  if (greeting) {
    var hour = new Date().getHours();
    var text = "hi";
    if (hour >= 5 && hour < 12) text = "good morning";
    else if (hour >= 12 && hour < 17) text = "good afternoon";
    else if (hour >= 17 && hour < 21) text = "good evening";
    greeting.textContent = text + ", i'm mo.";
  }

  var progress = document.createElement("div");
  progress.className = "scroll-progress";
  progress.setAttribute("aria-hidden", "true");
  document.body.appendChild(progress);
  function updateProgress() {
    var scrollTop = window.scrollY;
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    var scrollPercent = docHeight > 0 ? scrollTop / docHeight : 0;
    progress.style.transform = "scaleX(" + scrollPercent + ")";
  }
  window.addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();

  var toast = document.createElement("div");
  toast.className = "copy-toast";
  toast.textContent = "copied to clipboard";
  document.body.appendChild(toast);
  var emailLinks = document.querySelectorAll('a[href^="mailto:"]');
  emailLinks.forEach(function(link) {
    link.classList.add("email-link");
    link.addEventListener("click", function(e) {
      e.preventDefault();
      var email = link.href.replace("mailto:", "");
      navigator.clipboard.writeText(email).then(function() {
        toast.classList.add("show");
        setTimeout(function() {
          toast.classList.remove("show");
        }, 2000);
      });
    });
  });

  var moons = ["☾", "☽", "◐", "◑", "●", "○"];
  var moonIndex = 0;
  var footer = document.querySelector("footer");
  if (footer && footer.textContent.includes("☾")) {
    var html = footer.innerHTML;
    footer.innerHTML = html.replace("☾", '<span class="moon-toggle">☾</span>');
    var moonEl = footer.querySelector(".moon-toggle");
    if (moonEl) {
      moonEl.addEventListener("click", function() {
        moonIndex = (moonIndex + 1) % moons.length;
        moonEl.textContent = moons[moonIndex];
      });
    }
  }
})();
