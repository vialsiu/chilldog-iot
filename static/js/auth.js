(function () {
  function togglePw(btn) {
    const wrap = btn.closest(".pw-wrap");
    const input = wrap?.querySelector("input");
    if (!input) return;

    const isPw = input.type === "password";
    input.type = isPw ? "text" : "password";
    btn.textContent = isPw ? "Hide" : "Show";
    btn.setAttribute("aria-label", isPw ? "Hide password" : "Show password");
  }

  window.togglePw = togglePw;

  const tos = document.getElementById("tos");
  const createBtn = document.getElementById("createBtn");

  if (tos && createBtn) {
    function sync() {
      createBtn.disabled = !tos.checked;
      createBtn.classList.toggle("is-enabled", tos.checked);
    }
    tos.addEventListener("change", sync);
    sync();
  }
})();
