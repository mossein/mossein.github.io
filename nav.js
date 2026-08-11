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
    // "/" not "index.html" — Pages serves both, and linking one form keeps the
    // canonical, the analytics row, and the crawl path all pointing at one url
    { href: "/", label: "home" },
    { href: "blog.html", label: "blog" },
    { href: "links.html", label: "links" },
    { href: "photos.html", label: "photos" },
    // { href: "studio.html", label: "studio" }, // hidden for now
    { href: "now.html", label: "now" }
  ];
  var path = location.pathname.split("/").pop();
  var isHome = !path || path === "index.html";
  for (var i = 0; i < links.length; i++) {
    var a = document.createElement("a");
    a.href = links[i].href;
    a.textContent = links[i].label;
    // home is "/", so match it on the resolved page rather than the href; the
    // rest also answer without their extension, hence the second comparison
    var current = links[i].href === "/"
      ? isHome
      : (path === links[i].href || path === links[i].href.replace(".html", ""));
    if (current) {
      a.setAttribute("aria-current", "page");
    }
    nav.appendChild(a);
  }

  function currentTheme() {
    if (r.classList.contains("watercolor")) return "watercolor";
    if (r.classList.contains("dark")) return "dark";
    return "light";
  }

  var THEME_LABEL = {
    light: "Theme: light — switch to dark",
    dark: "Theme: dark — switch to watercolor",
    watercolor: "Theme: watercolor — switch to light"
  };

  function iconForTheme(theme) {
    // the glyph has to say which theme you're IN, otherwise nobody discovers
    // there's a third one behind the toggle
    var open = '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden="true" focusable="false">';
    if (theme === "dark") {
      // crescent
      return open + '<path d="M13.2 10.4A5.6 5.6 0 0 1 6 3.1a5.7 5.7 0 1 0 7.2 7.3z" ' +
        'fill="currentColor"/></svg>';
    }
    if (theme === "watercolor") {
      // droplet
      return open + '<path d="M8 1.6s4 4.3 4 7a4 4 0 0 1-8 0c0-2.7 4-7 4-7z" ' +
        'fill="currentColor" opacity="0.85"/></svg>';
    }
    // sun
    return open + '<circle cx="8" cy="8" r="3.1" fill="currentColor"/>' +
      '<g stroke="currentColor" stroke-width="1.3" stroke-linecap="round">' +
      '<path d="M8 1v1.6M8 13.4V15M1 8h1.6M13.4 8H15M3.1 3.1l1.1 1.1M11.8 11.8l1.1 1.1' +
      'M12.9 3.1l-1.1 1.1M4.2 11.8l-1.1 1.1"/></g></svg>';
  }

  function paintToggle() {
    var t = currentTheme();
    btn.innerHTML = iconForTheme(t);
    btn.setAttribute("aria-label", THEME_LABEL[t]);
    btn.setAttribute("title", THEME_LABEL[t]);
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
    if (window.gtag) window.gtag("event", "theme_change", { theme: theme });
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
    paintToggle();
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
  paintToggle();
  btn.addEventListener("click", function () {
    var c = currentTheme();
    var next = c === "light" ? "dark" : c === "dark" ? "watercolor" : "light";
    setTheme(next);
  });
  updatePortrait();
  nav.appendChild(btn);
  host.replaceWith(nav);

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
    // write into .typer-line so the marker stroke still has something to sit on
    (greeting.querySelector(".typer-line") || greeting).textContent =
      text + ", i'm mo.";
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
    link.title = "click to copy";
    link.addEventListener("click", function(e) {
      var email = link.href.replace("mailto:", "");
      if (!navigator.clipboard) return; // no clipboard — let the mailto happen
      e.preventDefault();
      navigator.clipboard.writeText(email).then(function() {
        toast.classList.add("show");
        setTimeout(function() {
          toast.classList.remove("show");
        }, 2000);
      }).catch(function() {
        // copying failed — don't swallow the click, fall back to the mail client
        window.location.href = link.href;
      });
    });
  });

  // --- Clips inside posts ---
  // they autoplay muted like a moving photograph, but a looping clip you can't
  // stop is a nuisance while reading, so clicking one holds it still
  var clips = document.querySelectorAll(".snap--clip video, .filmstrip video");
  Array.prototype.forEach.call(clips, function (v) {
    var frame = v.closest(".snap, .filmstrip");
    v.addEventListener("click", function () {
      if (v.paused) {
        v.play();
      } else {
        v.pause();
      }
    });
    v.addEventListener("play", function () {
      if (frame) frame.classList.remove("is-paused");
    });
    v.addEventListener("pause", function () {
      if (frame) frame.classList.add("is-paused");
    });
    // don't burn battery on a clip nobody is looking at
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            if (!v.dataset.held) v.play().catch(function () {});
          } else {
            v.pause();
          }
        });
      }, { threshold: 0.2 });
      io.observe(v);
      // a deliberate pause should survive scrolling away and back
      v.addEventListener("click", function () {
        v.dataset.held = v.paused ? "1" : "";
      });
    }
  });

  // --- Custom analytics events ---
  // pageviews alone couldn't answer "which links get clicked" or "does anyone
  // finish a post", which is most of what's worth knowing on a site this size
  function track(name, params) {
    if (window.gtag) window.gtag("event", name, params || {});
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (/^mailto:/.test(href)) {
      track("email_click", { address: href.replace("mailto:", "") });
      return;
    }
    var url;
    try { url = new URL(a.href, location.href); } catch (err) { return; }
    if (url.host && url.host !== location.host) {
      track("outbound_click", {
        destination: url.host,
        url: url.href,
        link_text: (a.textContent || "").trim().slice(0, 60)
      });
    }
  }, true);

  // read depth on posts only — a scroll milestone on the blog index means nothing
  var post = document.querySelector("article");
  if (post) {
    var marks = [25, 50, 75, 100];
    var hit = {};
    var slug = location.pathname.split("/").pop().replace(".html", "") || "index";
    window.addEventListener("scroll", function () {
      var box = post.getBoundingClientRect();
      var total = box.height - window.innerHeight;
      if (total <= 0) return;
      var pct = Math.min(100, Math.max(0, (-box.top / total) * 100));
      for (var i = 0; i < marks.length; i++) {
        var m = marks[i];
        if (pct >= m && !hit[m]) {
          hit[m] = true;
          track("read_depth", { post: slug, percent: m });
        }
      }
    }, { passive: true });
  }

  // --- Keyboard shortcuts ---
  document.addEventListener("keydown", function (e) {
    // skip if typing in an input/textarea
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      // mirrors the nav order so the numbers match what's on screen
      case "1": window.location.href = "index.html"; break;
      case "2": window.location.href = "blog.html"; break;
      case "3": window.location.href = "links.html"; break;
      case "4": window.location.href = "photos.html"; break;
      case "5": window.location.href = "now.html"; break;
      case "6": window.location.href = "studio.html"; break;
      case "t":
        var c = currentTheme();
        var next = c === "light" ? "dark" : c === "dark" ? "watercolor" : "light";
        setTheme(next);
        break;
    }
  });

  // --- Moon toggle (SVG-drawn, real phase) ---
  function getMoonPhase() {
    // simple lunar phase calculation
    var now = new Date();
    var year = now.getFullYear();
    var month = now.getMonth() + 1;
    var day = now.getDate();
    if (month <= 2) { year--; month += 12; }
    var a = Math.floor(year / 100);
    var b = 2 - a + Math.floor(a / 4);
    var jd = Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + b - 1524.5;
    var phase = ((jd - 2451550.1) / 29.530588853) % 1;
    if (phase < 0) phase += 1;
    return phase; // 0 = new, 0.5 = full
  }

  var moonPhase = getMoonPhase();
  var footer = document.querySelector("footer");
  if (footer && footer.textContent.includes("☾")) {
    var html = footer.innerHTML;
    var svgNS = "http://www.w3.org/2000/svg";
    // a real button so it's reachable by keyboard, not a click-only span
    footer.innerHTML = html.replace(
      "☾",
      '<button type="button" class="moon-toggle" aria-label="Moon phase — click to advance"></button>'
    );
    var moonEl = footer.querySelector(".moon-toggle");

    function drawMoon(phase) {
      var isDk = r.classList.contains("dark");
      var isWc = r.classList.contains("watercolor");
      var litColor = isDk ? "#ccc" : isWc ? "#8b8e92" : "#888";
      var bgColor = isDk ? "#000" : isWc ? "#faf7f1" : "#fff";

      // two-circle approach: lit moon + shadow circle offset
      // phase 0 = new (all dark), 0.5 = full (all lit)
      var offset;
      if (phase < 0.5) {
        // waxing: shadow circle moves from center to the right
        offset = -18 + phase * 2 * 36; // -18 to +18
      } else {
        // waning: shadow circle moves from right to center from left
        offset = 18 - (phase - 0.5) * 2 * 36; // +18 to -18
      }

      moonEl.innerHTML = '<svg width="12" height="12" viewBox="0 0 20 20" style="vertical-align:-1px">'
        + '<defs><mask id="moonmask">'
        + '<rect width="20" height="20" fill="white"/>'
        + '<circle cx="' + (10 + offset) + '" cy="10" r="9" fill="black"/>'
        + '</mask></defs>'
        + '<circle cx="10" cy="10" r="9" fill="' + litColor + '" mask="url(#moonmask)"/>'
        + '</svg>';
    }

    drawMoon(moonPhase);

    moonEl.addEventListener("click", function () {
      moonPhase = (moonPhase + (1 / 8)) % 1;
      drawMoon(moonPhase);
    });

    // redraw on theme change
    var moonObs = new MutationObserver(function () { drawMoon(moonPhase); });
    moonObs.observe(r, { attributes: true, attributeFilter: ["class"] });
  }
})();
