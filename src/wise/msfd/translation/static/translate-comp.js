$(document).ready(function(){

  var $original = $('#transl-original-text');
  var $old = $('#transl-old-translation');

  var editTranslation = function(e) {
    //e.preventDefault();
    var $cell = $(this).parents('td.translatable');

    var $text_div = $('.tr-text', $cell);
    var old_translation = $('.transl', $text_div).text();
    var orig_text = $('.text', $text_div).text();

    $original.text(orig_text);
    $old.text(old_translation);

    $('#form-edit-translation #new_transl').html(old_translation);

  };

  var submitTranslation = function(e) {
    e.preventDefault();

    var orig_text = $original.text();
    var $form = $('#form-edit-translation');
    var translation = $("#new_transl", form).html();

    $.ajax({
      form: $form,
      type: 'POST',
      url: './translate-callback',
      dataType: 'json',
      data: {
        'external-reference': orig_text,
        'translation': translation
      },
      success: function(result) {
        location.reload();
      },
      error: function(result) {
        alert('ERROR saving translation!');
      }
    });
  };

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
    // $(".autoTransl").on("click", autoTranslation);
    $('.editTransl').on("click", editTranslation);
    $('.submitTransl').on("click", submitTranslation);

    // todo: toggle clickability of buttons?
    $('.btn-translate-orig').on("click", toggleTranslations);
    $('.btn-translate-transl').on("click", toggleTranslations);
  };

  // setupTranslateClickHandlers();

});
