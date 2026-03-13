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
  });
})();
