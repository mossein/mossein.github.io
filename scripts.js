// Smooth scrolling effect when clicking on nav links
$(document).on('click', 'a[href^="#"]', function (event) {
  event.preventDefault();

  $('html, body').animate({
    scrollTop: $($.attr(this, 'href')).offset().top
  }, 500);
});

// Fade in effect for project images
$(document).ready(function () {
  $('.project-image').css('opacity', 0).fadeTo(1000, 1);
});

// Tooltip effect for skill badges
$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});
