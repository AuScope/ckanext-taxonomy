/**
 * Taxonomy tree expand/collapse behaviour.
 *
 * Clicking on a .taxonomy-toggle element toggles the next sibling
 * .taxonomy-children <ul> and rotates the caret icon.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var container = document.querySelector(".taxonomy-tree-container");
    if (!container) return;

    container.addEventListener("click", function (e) {
      var toggle = e.target.closest(".taxonomy-toggle");
      if (!toggle) return;

      // Prevent click from triggering the link
      e.preventDefault();
      e.stopPropagation();

      // Find the sibling <ul> list
      var parent = toggle.closest(".taxonomy-node-row, .taxonomy-node--root");
      if (!parent) return;

      var childList =
        parent.nextElementSibling ||
        parent.parentElement.querySelector(":scope > .taxonomy-children");

      if (!childList || !childList.classList.contains("taxonomy-children"))
        return;

      var isOpen = childList.style.display !== "none";
      childList.style.display = isOpen ? "none" : "block";
      toggle.classList.toggle("open", !isOpen);
    });

    /* ── Filter / search bar ───────────────────────────────── */
    var filterInput = document.getElementById("taxonomy-filter");
    if (!filterInput) return;

    var debounceTimer;
    filterInput.addEventListener("input", function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyFilter, 150);
    });

    function applyFilter() {
      var query = filterInput.value.trim().toLowerCase();

      // Reset visibility and collapse state when filter is cleared
      if (!query) {
        container.querySelectorAll(".taxonomy-root, .taxonomy-node").forEach(function (el) {
          el.style.display = "";
        });
        container.querySelectorAll(".taxonomy-children").forEach(function (ul) {
          ul.style.display = "none";
        });
        container.querySelectorAll(".taxonomy-toggle").forEach(function (t) {
          t.classList.remove("open");
        });
        return;
      }

      // 1. Hide everything, then selectively reveal matches + ancestors
      container.querySelectorAll(".taxonomy-root").forEach(function (root) {
        root.style.display = "none";
      });
      container.querySelectorAll(".taxonomy-node").forEach(function (node) {
        node.style.display = "none";
      });

      // 2. Find all labels matching the query
      container.querySelectorAll(".taxonomy-label").forEach(function (label) {
        if (label.textContent.toLowerCase().indexOf(query) === -1) return;

        // Show the matched element and all ancestors up to .taxonomy-root
        var el = label.closest(".taxonomy-node, .taxonomy-root");
        while (el) {
          el.style.display = "";
          // Expand parent <ul> so the match is visible
          var parentUl = el.closest(".taxonomy-children");
          if (parentUl) {
            parentUl.style.display = "block";
            var toggle = parentUl.previousElementSibling &&
              parentUl.previousElementSibling.querySelector(".taxonomy-toggle");
            if (toggle) toggle.classList.add("open");
          }
          el = el.parentElement ? el.parentElement.closest(".taxonomy-node, .taxonomy-root") : null;
        }
      });
    }
  });
})();
