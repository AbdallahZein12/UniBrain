// UniGraph tooltip logic (portal-based)
document.addEventListener("DOMContentLoaded", () => {
  const stage = document.getElementById("neoStage");
  const tip = document.getElementById("neoTooltip");

  if (!stage || !tip) return;

  function showTip(text, clientX, clientY) {
    tip.textContent = text;
    tip.classList.add("show");

    const pad = 12;
    const rect = tip.getBoundingClientRect();

    let left = clientX + 14;
    let top  = clientY + 14;

    if (left + rect.width > window.innerWidth - pad) {
      left = clientX - rect.width - 14;
    }
    if (top + rect.height > window.innerHeight - pad) {
      top = clientY - rect.height - 14;
    }

    tip.style.left = left + "px";
    tip.style.top  = top + "px";
  }

  function hideTip() {
    tip.classList.remove("show");
  }

  stage.querySelectorAll(".neo-node").forEach(node => {
    node.addEventListener("mousemove", (e) => {
      const text = node.getAttribute("data-tip");
      if (text) showTip(text, e.clientX, e.clientY);
    });

    node.addEventListener("mouseleave", hideTip);
  });
});
