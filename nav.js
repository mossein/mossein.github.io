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
    { href: "links.html", label: "links" },
    { href: "studio.html", label: "studio" },
    { href: "now.html", label: "now" }
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

  // --- Theme switch sounds ---
  var audioCtx = null;
  function getAudioCtx() {
    if (!audioCtx) {
      try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
    }
    return audioCtx;
  }

  function playThemeSound(theme) {
    var ctx = getAudioCtx();
    if (!ctx) return;
    try {
      if (theme === "light") {
        playTone(ctx, 880, 0.08, 0, "sine");
        playTone(ctx, 1100, 0.06, 0.08, "sine");
      } else if (theme === "dark") {
        playTone(ctx, 220, 0.1, 0, "triangle");
        playTone(ctx, 165, 0.08, 0.06, "triangle");
      } else {
        playWaterSplash(ctx);
      }
    } catch (e) {}
  }

  function playTone(ctx, freq, dur, delay, type) {
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = type || "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.06, ctx.currentTime + delay);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime + delay);
    osc.stop(ctx.currentTime + delay + dur + 0.01);
  }

  function playWaterSplash(ctx) {
    var bufferSize = ctx.sampleRate * 0.15;
    var buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.3;
    }
    var source = ctx.createBufferSource();
    source.buffer = buffer;
    var filter = ctx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.value = 2000;
    filter.Q.value = 0.5;
    var gain = ctx.createGain();
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);
    source.start();
  }

  // --- Clean up all watercolor-specific inline styles ---
  function clearWatercolorState() {
    document.body.style.backgroundImage = "";
    document.body.style.backgroundColor = "";
    if (blob2El) {
      blob2El.remove();
      blob2El = null;
    }
    // clear any paint trail canvases
    var trails = document.querySelectorAll(".paint-trail-canvas");
    trails.forEach(function (el) { el.remove(); });
  }

  function setTheme(theme) {
    playThemeSound(theme);
    // always clean watercolor state first
    clearWatercolorState();

    if (theme === "dark") {
      r.classList.add("dark");
      r.classList.remove("watercolor");
      localStorage.setItem("theme", "dark");
    } else if (theme === "watercolor") {
      r.classList.add("watercolor");
      r.classList.remove("dark");
      localStorage.setItem("theme", "watercolor");
      addBlob2();
      applyTimeOfDay();
      setupPaintTrail();
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

  // --- Cursor blob (base) ---
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

  // --- Paint trail (watercolor cursor effect) ---
  var trailCanvas = null;
  var trailCtx = null;
  var trailPoints = [];
  var lastTrailTime = 0;

  function setupPaintTrail() {
    if (trailCanvas) return;
    trailCanvas = document.createElement("canvas");
    trailCanvas.className = "paint-trail-canvas";
    trailCanvas.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:1;mix-blend-mode:multiply;opacity:0.35;";
    trailCanvas.width = window.innerWidth;
    trailCanvas.height = window.innerHeight;
    document.body.appendChild(trailCanvas);
    trailCtx = trailCanvas.getContext("2d");
    trailPoints = [];

    window.addEventListener("resize", function () {
      if (trailCanvas) {
        trailCanvas.width = window.innerWidth;
        trailCanvas.height = window.innerHeight;
      }
    });
  }

  var wcColors = [
    [121, 167, 255], [255, 174, 188], [168, 236, 195],
    [255, 200, 140], [200, 160, 255]
  ];

  document.addEventListener("mousemove", function (e) {
    if (!r.classList.contains("watercolor") || !trailCtx) return;
    var now = Date.now();
    if (now - lastTrailTime < 40) return;
    lastTrailTime = now;

    var col = wcColors[Math.floor(Math.random() * wcColors.length)];
    trailPoints.push({
      x: e.clientX,
      y: e.clientY,
      r: 8 + Math.random() * 16,
      col: col,
      alpha: 0.3 + Math.random() * 0.2,
      life: 1
    });
    if (trailPoints.length > 60) trailPoints.shift();
  });

  function fadeTrail() {
    if (!trailCtx || !r.classList.contains("watercolor")) {
      if (trailCtx) trailCtx.clearRect(0, 0, trailCanvas.width, trailCanvas.height);
      requestAnimationFrame(fadeTrail);
      return;
    }
    trailCtx.clearRect(0, 0, trailCanvas.width, trailCanvas.height);
    for (var i = trailPoints.length - 1; i >= 0; i--) {
      var p = trailPoints[i];
      p.life -= 0.008;
      if (p.life <= 0) { trailPoints.splice(i, 1); continue; }
      var grd = trailCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
      var a = p.alpha * p.life;
      grd.addColorStop(0, "rgba(" + p.col[0] + "," + p.col[1] + "," + p.col[2] + "," + a + ")");
      grd.addColorStop(0.6, "rgba(" + p.col[0] + "," + p.col[1] + "," + p.col[2] + "," + (a * 0.3) + ")");
      grd.addColorStop(1, "rgba(" + p.col[0] + "," + p.col[1] + "," + p.col[2] + ",0)");
      trailCtx.beginPath();
      trailCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      trailCtx.fillStyle = grd;
      trailCtx.fill();
    }
    requestAnimationFrame(fadeTrail);
  }
  fadeTrail();

  if (currentTheme() === "watercolor") setupPaintTrail();

  // --- Second watercolor blob layer ---
  var blob2El = null;
  function addBlob2() {
    if (blob2El) return;
    blob2El = document.createElement("div");
    blob2El.className = "watercolor-blob-2";
    document.body.appendChild(blob2El);
  }
  if (currentTheme() === "watercolor") addBlob2();


  // --- Time-of-day watercolor ---
  function applyTimeOfDay() {
    if (!r.classList.contains("watercolor")) return;
    var hour = new Date().getHours();
    var bgColor, blobs;
    if (hour >= 5 && hour < 10) {
      // morning — warm peach and gold
      bgColor = "#fdf6ed";
      blobs = "radial-gradient(1200px 800px at 8% 12%, rgba(255, 200, 120, 0.3), transparent 60%),"
        + "radial-gradient(1000px 700px at 85% 18%, rgba(255, 160, 140, 0.25), transparent 60%),"
        + "radial-gradient(900px 620px at 25% 85%, rgba(255, 220, 160, 0.22), transparent 60%),"
        + "radial-gradient(600px 400px at 60% 40%, rgba(255, 190, 100, 0.18), transparent 65%),"
        + "radial-gradient(1400px 900px at 50% 50%, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7))";
    } else if (hour >= 10 && hour < 16) {
      // midday — bright, balanced (default palette basically)
      bgColor = "#faf7f1";
      blobs = "radial-gradient(1200px 800px at 8% 12%, rgba(121, 167, 255, 0.22), transparent 60%),"
        + "radial-gradient(1000px 700px at 85% 18%, rgba(255, 174, 188, 0.22), transparent 60%),"
        + "radial-gradient(900px 620px at 25% 85%, rgba(168, 236, 195, 0.2), transparent 60%),"
        + "radial-gradient(600px 400px at 70% 50%, rgba(200, 160, 255, 0.14), transparent 65%),"
        + "radial-gradient(1400px 900px at 50% 50%, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8))";
    } else if (hour >= 16 && hour < 20) {
      // golden hour — deep amber, rose, warm purple
      bgColor = "#faf3ea";
      blobs = "radial-gradient(1200px 800px at 10% 20%, rgba(255, 140, 80, 0.3), transparent 60%),"
        + "radial-gradient(1000px 700px at 80% 15%, rgba(255, 120, 140, 0.28), transparent 60%),"
        + "radial-gradient(900px 620px at 30% 80%, rgba(200, 140, 255, 0.2), transparent 60%),"
        + "radial-gradient(600px 400px at 65% 50%, rgba(255, 180, 60, 0.22), transparent 65%),"
        + "radial-gradient(1400px 900px at 50% 50%, rgba(255, 252, 245, 0.75), rgba(255, 252, 245, 0.75))";
    } else {
      // night — deep blues, indigo, soft moonlight
      bgColor = "#f0f0f6";
      blobs = "radial-gradient(1200px 800px at 8% 12%, rgba(80, 100, 200, 0.3), transparent 60%),"
        + "radial-gradient(1000px 700px at 85% 18%, rgba(120, 100, 180, 0.25), transparent 60%),"
        + "radial-gradient(900px 620px at 25% 85%, rgba(100, 140, 200, 0.22), transparent 60%),"
        + "radial-gradient(600px 400px at 70% 50%, rgba(160, 120, 220, 0.18), transparent 65%),"
        + "radial-gradient(1400px 900px at 50% 50%, rgba(240, 240, 250, 0.8), rgba(240, 240, 250, 0.8))";
    }
    document.body.style.backgroundColor = bgColor;
    document.body.style.backgroundImage = blobs;
  }
  if (currentTheme() === "watercolor") applyTimeOfDay();

  // --- Reveal observer ---
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

  // --- Reading time ---
  var article = document.querySelector("article");
  if (article) {
    var words = article.textContent.trim().split(/\s+/).length;
    var mins = Math.max(1, Math.round(words / 230));
    var dateEl = article.querySelector(".date");
    if (dateEl) {
      var span = document.createElement("span");
      span.className = "reading-time";
      span.textContent = " · " + mins + " min read";
      dateEl.appendChild(span);
    }
  }

  // --- Time-based greeting ---
  var greeting = document.getElementById("greeting");
  if (greeting) {
    var hour = new Date().getHours();
    var text = "hi";
    if (hour >= 5 && hour < 12) text = "good morning";
    else if (hour >= 12 && hour < 17) text = "good afternoon";
    else if (hour >= 17 && hour < 21) text = "good evening";
    greeting.textContent = text + ", i'm mo.";
  }

  // --- Scroll progress ---
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

  // --- Copy email ---
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

  // --- Keyboard shortcuts ---
  document.addEventListener("keydown", function (e) {
    // skip if typing in an input/textarea
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      case "1": window.location.href = "index.html"; break;
      case "2": window.location.href = "blog.html"; break;
      case "3": window.location.href = "links.html"; break;
      case "4": window.location.href = "studio.html"; break;
      case "5": window.location.href = "now.html"; break;
      case "t":
        var c = currentTheme();
        var next = c === "light" ? "dark" : c === "dark" ? "watercolor" : "light";
        setTheme(next);
        break;
    }
  });

  // --- Moon toggle ---
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
