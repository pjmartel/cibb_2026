(() => {
  const data = document.querySelector("#slide-data");
  if (!data) return;
  const slides = JSON.parse(data.textContent);
  const image = document.querySelector("#current-slide");
  const selector = document.querySelector("#slide-select");
  const previous = document.querySelector("[data-slide-previous]");
  const next = document.querySelector("[data-slide-next]");
  const label = document.querySelector("[data-slide-label]");
  const notice = document.querySelector("[data-slide-notice]");
  const imageLink = document.querySelector("[data-slide-image]");
  const svgLink = document.querySelector("[data-slide-svg]");
  let current = 0;
  function show(index, updateHash = true) {
    current = Math.max(0, Math.min(slides.length - 1, index));
    const slide = slides[current];
    image.src = `assets/slides/${slide.file_stem}.png`;
    image.alt = `Slide ${slide.slide}: ${slide.title}`;
    selector.value = String(current);
    previous.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    label.textContent = `${String(slide.slide).padStart(2, "0")} / ${slides.length} · ${slide.title} · ${slide.lecture_time}`;
    imageLink.href = `assets/slides/${slide.file_stem}.png`;
    svgLink.href = `assets/slides/${slide.file_stem}.svg`;
    document.querySelectorAll("[data-slide-index]").forEach((button) => {
      button.setAttribute("aria-current", String(Number(button.dataset.slideIndex) === current));
    });
    notice.textContent = "";
    if (updateHash) {
      try { history.replaceState(null, "", `#slide-${slide.slide}`); }
      catch { /* The viewer still works when history APIs are restricted. */ }
    }
  }
  function fromHash() {
    const match = location.hash.match(/^#slide-(\d+)$/);
    show(match ? Number(match[1]) - 1 : 0, false);
  }
  previous.addEventListener("click", () => show(current - 1));
  next.addEventListener("click", () => show(current + 1));
  selector.addEventListener("change", () => show(Number(selector.value)));
  document.querySelectorAll("[data-slide-index]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      show(Number(button.dataset.slideIndex));
      document.querySelector(".slide-frame").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  document.addEventListener("keydown", (event) => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName) || event.altKey || event.ctrlKey || event.metaKey) return;
    if (["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      show(event.key === "Home" ? 0 : event.key === "End" ? slides.length - 1 :
        current + (event.key === "ArrowRight" ? 1 : -1));
    }
  });
  window.addEventListener("hashchange", fromHash);
  image.addEventListener("error", () => {
    notice.textContent = "This slide image could not load. Try the SVG link or download the slide bundle.";
  });
  fromHash();
})();
