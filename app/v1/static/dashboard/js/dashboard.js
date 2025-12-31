(function () {
  const input = document.getElementById("composerInput");

  function autosize(el) {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  if (input) {
    autosize(input);
    input.addEventListener("input", () => autosize(input));

    // Enter sends, Shift+Enter newline (frontend feel; backend wiring later)
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        const form = input.closest("form");
        if (form) {
          e.preventDefault();
          form.requestSubmit();
        }
      }
    });
  }

  // Suggestion cards: copy prompt into composer
  document.querySelectorAll("[data-suggest]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-suggest") || "";
      if (!input) return;
      input.value = text;
      autosize(input);
      input.focus();
    });
  });

  // Fake active highlighting (for design only)
  const sessionList = document.getElementById("sessionList");
  if (sessionList) {
    sessionList.addEventListener("click", (e) => {
      const a = e.target.closest(".session-item");
      if (!a) return;
      sessionList.querySelectorAll(".session-item").forEach((x) => x.classList.remove("is-active"));
      a.classList.add("is-active");
      e.preventDefault();
    });
  }

  // New chat button (design only)
  const newChatBtn = document.getElementById("newChatBtn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
      if (!input) return;
      input.value = "";
      autosize(input);
      input.focus();
    });
  }
})();
