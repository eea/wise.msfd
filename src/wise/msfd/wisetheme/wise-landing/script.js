document.addEventListener("DOMContentLoaded", function() {
  var container = document.querySelectorAll(".landing-section");
  var winHeight =
    window.innerHeight ||
    document.documentElement.clientHeight ||
    document.body.clientHeight;

  for (var i = 0; i < container.length; i++) {
    var element = container[i];
    element.style.minHeight = winHeight + "px";
  }

  document.getElementById("privacy-modal").onclick = function openModal() {
    document.getElementsByClassName("wise-modal")[0].style.display = "block";
    document
      .getElementsByClassName("landing-page")[0]
      .classList.add("has-modal-open");
  };

  document.getElementById("close-modal").onclick = function closeModal() {
    document.getElementsByClassName("wise-modal")[0].style.display = "none";
    document
      .getElementsByClassName("landing-page")[0]
      .classList.remove("has-modal-open");
  };
});
