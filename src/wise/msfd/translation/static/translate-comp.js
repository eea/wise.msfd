$(document).ready(function(){

  var $original = $('#transl-original-text');
  var $old = $('#transl-old-translation');

  var editTranslation = function(e) {
    // inline editing in report data view page
    // e.preventDefault();
    var $cell = $(this).parents('td.translatable');

    var $text_div = $('.tr-text', $cell);
    var old_translation = $('.transl', $text_div).text();
    var orig_text = $('.text', $text_div).text();

    $original.text(orig_text);
    $old.text(old_translation);

    var $textarea = $('#form-edit-translation #new_transl');
    $textarea.val(old_translation.trim());

  };

  var submitTranslation = function(e) {
    // inline editing in report data view page
    e.preventDefault();

    var orig_text = $original.text();
    var $form = $('#form-edit-translation');
    var translation = $("#new_transl", $form).html();

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

  setupTranslateClickHandlers();





    //
    //   jQuery(document).ready(function(){
    //     var $form = $('#form-edit-translation');
    //     var $modal = $('#edit-translation');
    //
    //     $modal.on('show.bs.modal', function(event) {
    //
    //       $form.off('submit');
    //
    //       // setup the modal to show proper values
    //       var $btn = $(event.relatedTarget);
    //       var cells = $btn.parent().parent().children();
    //
    //       var original = $(cells[0]).text();
    //       var translated = $(cells[1]).text();
    //
    //       $('#tr-original').text(original);   // show original text
    //       $('textarea[name="original"]', $form).val(original);   // form input
    //
    //       $('#tr-current').text(translated);    // show current translation
    //       $('#tr-new').val(translated);    // textarea for new translation
    //
    //       $form.on('submit', function() {
    //         var url = $form.attr('action');
    //         var data = {};
    //
    //         $('textarea,input', $form).each(function(){
    //           var name = $(this).attr('name');
    //           if (!name) return;
    //           data[name] = $(this).val();
    //         });
    //
    //         $.post(url, data, function(resp) {
    //           $modal.modal('hide');
    //           var $cell = $(cells[1]);
    //           $cell.hide();
    //           $cell.text(resp['text']);
    //           $cell.fadeIn(1000);
    //         });
    //
    //         return false;
    //       });
    //
    //   });
    // });




});
