// Проверка форм на странице: сообщения под полями вместо всплывающих подсказок браузера.
// Сервер проверяет то же самое заново, это только удобство.
const MESSAGES = {
  valueMissing: () => "Заполните это поле",
  typeMismatch: () => "Проверьте формат",
  patternMismatch: (el) => el.title || "Проверьте формат",
  tooShort: (el) => "Минимум символов: " + el.minLength,
  tooLong: (el) => "Максимум символов: " + el.maxLength,
};

function messageFor(el) {
  for (const key of Object.keys(MESSAGES)) {
    if (el.validity[key]) return MESSAGES[key](el);
  }
  return "";
}

function showError(el, text) {
  const box = el.closest("label").querySelector(".field-error");
  if (box) box.textContent = text;
  if (text) el.setAttribute("aria-invalid", "true");
  else el.removeAttribute("aria-invalid");
}

document.querySelectorAll("form[data-validate]").forEach((form) => {
  form.noValidate = true;
  const fields = form.querySelectorAll("input:not([type=hidden]), select, textarea");

  const check = (el) => {
    let text = messageFor(el);
    if (!text && el.name === "password2") {
      const first = form.querySelector("[name=password]");
      if (first && first.value !== el.value) text = "Пароли не совпадают";
    }
    showError(el, text);
    return !text;
  };

  fields.forEach((el) => {
    el.addEventListener("blur", () => { if (el.value !== "") check(el); });
    el.addEventListener("input", () => { if (el.getAttribute("aria-invalid")) check(el); });
  });

  form.addEventListener("submit", (event) => {
    let ok = true;
    let firstBad = null;
    fields.forEach((el) => {
      if (!check(el)) { ok = false; firstBad = firstBad || el; }
    });
    if (!ok) {
      event.preventDefault();
      firstBad.focus();
    }
  });
});
