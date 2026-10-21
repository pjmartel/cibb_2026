document.documentElement.classList.add("js");
const toggle = document.querySelector("[data-menu]");
const nav = document.querySelector(".main-nav");
toggle?.addEventListener("click", () => {
  const open = toggle.getAttribute("aria-expanded") !== "true";
  toggle.setAttribute("aria-expanded", String(open));
  nav.classList.toggle("is-open", open);
  toggle.textContent = open ? "Close menu" : "Menu";
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && toggle?.getAttribute("aria-expanded") === "true") toggle.click();
});
const search = document.querySelector("#resource-search");
const category = document.querySelector("#resource-category");
const entries = [...document.querySelectorAll("[data-resource]")];
function filterResources() {
  const query = (search?.value || "").trim().toLowerCase();
  const group = category?.value || "All";
  let count = 0;
  entries.forEach((entry) => {
    const visible = entry.textContent.toLowerCase().includes(query) &&
      (group === "All" || entry.dataset.category === group);
    entry.hidden = !visible;
    if (visible) count++;
  });
  const countLabel = document.querySelector("[data-resource-count]");
  if (countLabel) countLabel.textContent = `${count} resource${count === 1 ? "" : "s"}`;
  const empty = document.querySelector("[data-empty]");
  if (empty) empty.hidden = count !== 0;
}
search?.addEventListener("input", filterResources);
category?.addEventListener("change", filterResources);
document.querySelector("[data-reset-resources]")?.addEventListener("click", () => {
  search.value = "";
  category.value = "All";
  filterResources();
  search.focus();
});
document.querySelectorAll("img").forEach((image) => {
  image.addEventListener("error", () => {
    if (image.id === "current-slide") return;
    const fallback = document.createElement("p");
    fallback.className = "img-fallback";
    fallback.textContent = image.alt || "Image unavailable.";
    fallback.setAttribute("role", "img");
    fallback.setAttribute("aria-label", image.alt || "Image unavailable");
    image.replaceWith(fallback);
  }, { once: true });
});
if (entries.length) filterResources();
