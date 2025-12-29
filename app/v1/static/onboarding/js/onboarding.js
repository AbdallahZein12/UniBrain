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
    <input type="text" class="course-input" placeholder="CS 101" value="${escapeHtml(value)}" />
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

function addTerm(bucket) {
  if (!TERM_CONTAINER_BY_BUCKET[bucket]) {
    // fallback safety
    bucket = "completed";
  }

  const container = document.getElementById(TERM_CONTAINER_BY_BUCKET[bucket]);

  const card = document.createElement("div");
  card.className = "term-card";
  card.dataset.bucket = bucket;

  card.innerHTML = `
    <div class="term-head">
      <input type="text" placeholder="Fall 2024" class="term-input" />
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

  // remove term card
  card.querySelector(".term-remove").addEventListener("click", () => card.remove());

  // add single blank course
  card.querySelector(".chip-add").addEventListener("click", () => addCourse(card));

  // add many via comma/space/newline separated input
  card.querySelector(".chip-add-multi").addEventListener("click", () => {
    const raw = prompt("Paste courses (comma / space / newline separated):", "CS 101, MATH 205");
    if (!raw) return;
    raw
      .split(/[\n,]+/)
      .map(s => s.trim())
      .filter(Boolean)
      .forEach(code => addCourse(card, code));
  });

  container.appendChild(card);

  // Start with one empty chip so it’s obvious what to do
  addCourse(card);
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
