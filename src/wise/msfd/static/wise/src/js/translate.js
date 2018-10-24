//
function set_translatable(i, node) {
  $(node).mouseenter(
    function() {
      $(this).css(
        'background-color', 'red'
      )
    });
}

jQuery(document).ready(function() {
  $('.translatable').each(set_translatable);
});
