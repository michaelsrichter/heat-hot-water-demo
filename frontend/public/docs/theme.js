(() => {
  const root = document.documentElement;
  const saved = localStorage.getItem("hpd-docs-theme");
  const initial =
    saved === "dark" || saved === "light"
      ? saved
      : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";

  function setTheme(theme) {
    root.dataset.theme = theme;
    localStorage.setItem("hpd-docs-theme", theme);
    const button = document.querySelector("[data-theme-toggle]");
    const label = document.querySelector("[data-theme-label]");
    if (!button || !label) return;
    const next = theme === "dark" ? "light" : "dark";
    label.textContent = next === "dark" ? "Dark" : "Light";
    button.setAttribute("aria-label", `Use ${next} mode`);
  }

  setTheme(initial);
  document
    .querySelector("[data-theme-toggle]")
    ?.addEventListener("click", () => {
      setTheme(root.dataset.theme === "dark" ? "light" : "dark");
    });
})();
