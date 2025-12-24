function addTerm(type) {
  const container = document.getElementById(
    type === "completed" ? "completed-terms" : "in-progress-terms"
  );

  const div = document.createElement("div");
  div.className = "term-row";

  div.innerHTML = `
    <input type="text" placeholder="Fall 2024" class="term">
    <input type="text" placeholder="CS101, MATH205" class="courses">
    <button type="button" class="remove" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(div);
}

function buildCoursesJson() {
  const data = { completed: [], in_progress: [] };

  function collect(type, key) {
    document.querySelectorAll(`#${type}-terms .term-row`).forEach(row => {
      const term = row.querySelector(".term").value.trim();
      const courses = row.querySelector(".courses").value
        .split(",")
        .map(c => c.trim())
        .filter(Boolean)
        .slice(0, 8);

      if (term && courses.length) {
        data[key].push({ term, courses });
      }
    });
  }

  collect("completed", "completed");
  collect("in-progress", "in_progress");

  document.getElementById("courses-json").value = JSON.stringify(data);
}
