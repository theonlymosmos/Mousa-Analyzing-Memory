(function () {
  "use strict";

  // ---------- filter box ----------
  var input = document.getElementById("filter-input");
  var countEl = document.getElementById("filter-count");
  var rows = Array.prototype.slice.call(document.querySelectorAll(".row[data-phase-key]"));
  var toggles = Array.prototype.slice.call(document.querySelectorAll(".phase-toggle"));
  var searchCache = new WeakMap();

  function searchText(row) {
    var cached = searchCache.get(row);
    if (cached === undefined) {
      cached = row.textContent.toLowerCase();
      searchCache.set(row, cached);
    }
    return cached;
  }

  function activePhases() {
    var active = toggles.filter(function (t) { return t.getAttribute("aria-pressed") === "true"; });
    if (active.length === 0) return null; // null = no phase filter applied
    return active.map(function (t) { return t.dataset.phase; });
  }

  function applyFilter() {
    if (!rows.length) return;
    var q = (input && input.value ? input.value : "").trim().toLowerCase();
    var phases = activePhases();
    var shown = 0;
    rows.forEach(function (row) {
      var matchesText = !q || searchText(row).indexOf(q) !== -1;
      var matchesPhase = !phases || phases.indexOf(row.dataset.phaseKey) !== -1;
      var visible = matchesText && matchesPhase;
      row.classList.toggle("is-hidden", !visible);
      if (visible) shown++;
    });
    document.querySelectorAll(".phase-section").forEach(function (section) {
      var visibleRows = section.querySelectorAll(".row:not(.is-hidden)");
      section.classList.toggle("is-hidden", visibleRows.length === 0);
    });
    if (countEl) countEl.textContent = shown + " of " + rows.length + " plugins";
  }

  if (input) {
    input.addEventListener("input", applyFilter);
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input) {
        e.preventDefault();
        input.focus();
      } else if (e.key === "Escape" && document.activeElement === input) {
        input.value = "";
        applyFilter();
        input.blur();
      }
    });
  }

  toggles.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var pressed = btn.getAttribute("aria-pressed") === "true";
      btn.setAttribute("aria-pressed", String(!pressed));
      applyFilter();
    });
  });

  applyFilter();

  // ---------- copy buttons ----------
  function copyText(text, btn) {
    var done = function () {
      var original = btn.textContent;
      btn.textContent = "Copied";
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = original;
        btn.classList.remove("copied");
      }, 1000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text, done); });
    } else {
      fallbackCopy(text, done);
    }
  }

  function fallbackCopy(text, done) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* no-op */ }
    document.body.removeChild(ta);
    done();
  }

  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.dataset.copyTarget);
      if (target) copyText(target.textContent, btn);
    });
  });

  // ---------- deep-link row highlight ----------
  function flashTarget() {
    if (!location.hash) return;
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!el || !el.classList.contains("row")) return;
    el.classList.add("flash");
    el.scrollIntoView({ block: "center" });
    setTimeout(function () { el.classList.remove("flash"); }, 2000);
  }
  flashTarget();
  window.addEventListener("hashchange", flashTarget);

  // ---------- phase spine: current-section tracking ----------
  var spineLinks = Array.prototype.slice.call(document.querySelectorAll(".phase-list a"));
  var sections = Array.prototype.slice.call(document.querySelectorAll(".phase-section"));
  if (spineLinks.length && sections.length && "IntersectionObserver" in window) {
    var linkById = {};
    spineLinks.forEach(function (a) {
      linkById[a.getAttribute("href").slice(1)] = a;
    });
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          var link = linkById[entry.target.id];
          if (!link) return;
          if (entry.isIntersecting) {
            spineLinks.forEach(function (a) { a.parentElement.classList.remove("current"); });
            link.parentElement.classList.add("current");
          }
        });
      },
      { rootMargin: "-10% 0px -70% 0px", threshold: 0 }
    );
    sections.forEach(function (s) { observer.observe(s); });
  }

  // ---------- mobile page select ----------
  var pageSelect = document.getElementById("page-select");
  if (pageSelect) {
    pageSelect.addEventListener("change", function () {
      if (pageSelect.value) window.location.href = pageSelect.value;
    });
  }
})();
