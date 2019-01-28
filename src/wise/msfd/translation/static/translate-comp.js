$(document).ready(function(){

  var $original = $('#transl-original-text');
  var $old = $('#transl-old-translation');

  var toggleTranslations = function(e) {
    // setup the translations in the report data view screens
    $(this).toggleClass('active');
    $(this).siblings('.btn-translate').toggleClass('active');

    var $cell = $(this).parents('td.translatable');
    $cell
      .toggleClass('blue')
      .toggleClass('green')
    ;

    $('.text', $cell).toggleClass('active');
    $('.transl', $cell).toggleClass('active');

    var $tr = $(this).parents('tr');
    $tr.fixTableHeaderHeight();
  };

  window.setupTranslateClickHandlers = function() {
    // todo: toggle clickability of buttons?
    $('.btn-translate-orig').on("click", toggleTranslations);
    $('.btn-translate-transl').on("click", toggleTranslations);
  };

  setupTranslateClickHandlers();

});
