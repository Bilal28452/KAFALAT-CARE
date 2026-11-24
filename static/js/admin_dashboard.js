(function () {
  const sidebar = document.querySelector("[data-admin-sidebar]");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const searchInput = document.querySelector("[data-dashboard-search]");
  const searchableRows = () => Array.from(document.querySelectorAll("[data-search-row]"));
  const emptyState = document.querySelector("[data-empty-search-state]");

  sidebarToggle?.addEventListener("click", () => {
    sidebar?.classList.toggle("show");
  });

  document.querySelectorAll(".sidebar-nav a").forEach((link) => {
    link.addEventListener("click", () => sidebar?.classList.remove("show"));
  });

  searchInput?.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();
    let visibleCount = 0;

    searchableRows().forEach((row) => {
      const matches = row.textContent.toLowerCase().includes(query);
      row.classList.toggle("d-none", !matches);
      if (matches) visibleCount += 1;
    });

    if (emptyState) {
      emptyState.style.display = visibleCount === 0 && query ? "block" : "none";
    }
  });

  document.querySelectorAll("[data-bs-toggle='tooltip']").forEach((element) => {
    new bootstrap.Tooltip(element);
  });
})();
