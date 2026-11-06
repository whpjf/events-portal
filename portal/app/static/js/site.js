// кнопка «Меню» на телефоне
const button = document.querySelector(".menu-btn");
const nav = document.getElementById("nav");
if (button && nav) {
  button.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    button.setAttribute("aria-expanded", open ? "true" : "false");
  });
}
