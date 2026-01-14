// UniBrain Onboarding – term cards + course chips

const TERM_CONTAINER_BY_BUCKET = {
  completed: "completed-terms",
  in_progress: "in-progress-terms",
};

function addCourse(termCardEl, value = "") {
  const chips = termCardEl.querySelector(".course-chips");

  const chip = document.createElement("div");
  chip.className = "course-chip";
  chip.innerHTML = `
    <input type="text" class="course-input" placeholder="CS 201" value="${escapeHtml(value)}" />
    <button type="button" class="chip-remove" title="Remove course">−</button>
  `;

  chip.querySelector(".chip-remove").addEventListener("click", () => chip.remove());

  // Enter → create next chip (nice UX)
  chip.querySelector(".course-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addCourse(termCardEl);
      // focus newly created chip input
      const inputs = termCardEl.querySelectorAll(".course-input");
      inputs[inputs.length - 1]?.focus();
    }
  });

  chips.appendChild(chip);
}
function addTerm(bucket, termValue = "", coursesList = null) {
  if (!TERM_CONTAINER_BY_BUCKET[bucket]) {
    bucket = "completed";
  }

  const container = document.getElementById(TERM_CONTAINER_BY_BUCKET[bucket]);

  const card = document.createElement("div");
  card.className = "term-card";
  card.dataset.bucket = bucket;

  card.innerHTML = `
    <div class="term-head">
      <input type="text" placeholder="Fall 2024" class="term-input" value="${escapeHtml(termValue)}" />
      <button type="button" class="term-remove" title="Remove term">✕</button>
    </div>

    <div class="term-body">
      <div class="course-chips"></div>

      <div class="term-actions">
        <button type="button" class="chip-add">+ Add Course</button>
        <button type="button" class="chip-add-multi">+ Add Many</button>
      </div>
    </div>
  `;

  card.querySelector(".term-remove").addEventListener("click", () => card.remove());
  card.querySelector(".chip-add").addEventListener("click", () => addCourse(card));

  card.querySelector(".chip-add-multi").addEventListener("click", () => {
    const raw = prompt("Paste courses (comma / space / newline separated):", "CS 201, MATH 205");
    if (!raw) return;
    raw
      .split(/[\n,]+/)
      .map(s => s.trim())
      .filter(Boolean)
      .forEach(code => addCourse(card, code));
  });

  container.appendChild(card);

  // If we’re hydrating, add those courses; otherwise start with one empty chip.
  if (Array.isArray(coursesList) && coursesList.length) {
    coursesList.forEach(code => addCourse(card, code));
  } else {
    addCourse(card);
  }
}
function buildCoursesJson() {
  const data = { completed: [], in_progress: [] };

  function collect(bucketKey, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.querySelectorAll(".term-card").forEach((card) => {
      const term = card.querySelector(".term-input")?.value.trim() || "";

      const courses = Array.from(card.querySelectorAll(".course-input"))
        .map((inp) => inp.value.trim())
        .filter(Boolean);

      if (term && courses.length) {
        data[bucketKey].push({ term, courses });
      }
    });
  }

  collect("completed", TERM_CONTAINER_BY_BUCKET.completed);
  collect("in_progress", TERM_CONTAINER_BY_BUCKET.in_progress);

  document.getElementById("courses-json").value = JSON.stringify(data);
}

/** basic HTML escaping for values inserted into attributes */
function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

document.addEventListener("DOMContentLoaded", () => {
  const data = window.__PROFILE_COURSES__ || { completed: [], in_progress: [] };

  // Hydrate completed
  (data.completed || []).forEach(row => {
    addTerm("completed", row.term || "", row.courses || []);
  });

  // Hydrate in-progress
  (data.in_progress || []).forEach(row => {
    addTerm("in_progress", row.term || "", row.courses || []);
  });

  // If no saved data, start with one blank term in each bucket (nice UX)
  if ((data.completed || []).length === 0) addTerm("completed");
  if ((data.in_progress || []).length === 0) addTerm("in_progress");
});


function collectCoursesByTerm() {
  const data = { completed: [], in_progress: [] };

  function collect(bucketKey, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.querySelectorAll(".term-card").forEach((card) => {
      const term = card.querySelector(".term-input")?.value.trim() || "";
      const courses = Array.from(card.querySelectorAll(".course-input"))
        .map((inp) => inp.value.trim())
        .filter(Boolean);

      if (term && courses.length) data[bucketKey].push({ term, courses });
    });
  }

  collect("completed", TERM_CONTAINER_BY_BUCKET.completed);
  collect("in_progress", TERM_CONTAINER_BY_BUCKET.in_progress);

  return data;
}
function renderCourseCheck({ unknown_courses, suggestions }) {
  const box = document.getElementById("course-check-results");
  if (!box) return;

  if (!unknown_courses || unknown_courses.length === 0) {
    box.innerHTML = `
      <div class="ub-alert ub-alert--success">
        <h3>All set</h3>
        <p>All courses were recognized ✅</p>
      </div>
    `;
    return;
  }

  const rows = unknown_courses.map(code => {
    const opts = (suggestions && suggestions[code]) ? suggestions[code] : [];

    const chips = opts.length
      ? `<div class="suggestion-chips">
          ${opts.map(s => `
            <button type="button" class="suggest-btn" data-from="${escapeHtml(code)}" data-to="${escapeHtml(s)}">
              ${escapeHtml(s)}
            </button>
          `).join("")}
        </div>`
      : `<div class="muted">No close matches found.</div>`;

    return `
      <div class="unknown-row">
        <div class="unknown-code">${escapeHtml(code)}</div>
        <div class="unknown-meta">
          <div class="suggestion-label">Did you mean:</div>
          ${chips}
          <div class="muted">Click a suggestion to replace it in your form.</div>
        </div>
      </div>
    `;
  }).join("");

  box.innerHTML = `
    <div class="ub-alert ub-alert--warn">
      <h3>Some courses weren’t recognized</h3>
      <p>We’ll still let you save, but these won’t count toward requirement checks until they match the catalog.</p>
      <div class="unknown-list">${rows}</div>
    </div>
  `;
}

// Replace all occurrences of FROM -> TO across chips
function applySuggestion(from, to) {
  const norm = s => String(s).toUpperCase().replace(/\s+/g, " ").trim();

  document.querySelectorAll(".course-input").forEach(inp => {
    if (norm(inp.value) === norm(from)) inp.value = to;
  });
}

document.addEventListener("click", (e) => {
  const btn = e.target.closest(".suggest-btn");
  if (!btn) return;
  applySuggestion(btn.dataset.from, btn.dataset.to);
});

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("check-courses-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const payload = { courses_by_term: collectCoursesByTerm() };

    const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
    const url = window.__VALIDATE_COURSES_URL__;
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(csrf ? { "X-CSRFToken": csrf } : {})
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!data.ok) {
      renderCourseCheck({ unknown_courses: [], suggestions: {} });
      const box = document.getElementById("course-check-results");
      if (box) box.innerHTML = `<div class="alert alert-danger">${escapeHtml(data.error || "Validation failed")}</div>`;
      return;
    }

    renderCourseCheck(data);
  });
});

btn.addEventListener("click", async () => {
  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = "Checking…";

  try {
    // fetch logic...
  } finally {
    btn.disabled = false;
    btn.textContent = old;
  }
});