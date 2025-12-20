document.addEventListener("DOMContentLoaded", () => {
  const toggles = document.querySelectorAll("[data-password-toggle]");

  toggles.forEach((toggle) => {
    const wrapper = toggle.closest(".password-input");
    const input = wrapper?.querySelector("input");

    if (!input) return;

    toggle.addEventListener("click", () => {
      const willShow = input.type === "password";
      input.type = willShow ? "text" : "password";

      toggle.setAttribute("aria-pressed", willShow ? "true" : "false");
      toggle.setAttribute("aria-label", willShow ? "Hide password" : "Show password");
      toggle.textContent = willShow ? "Hide" : "Show";
    });
  });
});
