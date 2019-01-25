$(document).ready(function(){

  var autoTranslation = function(e) {
    e.preventDefault();

    var text = $(this).parents('td.translatable').find('.tr.text').text();
    var target_languages = ['EN'];
    // var source_lang = 'EN';

    $.ajax({
      type: "POST",
      url: "./@@translate-text",
      dataType: 'json',
      data: {
        "text-to-translate": text,
        "targetLanguages": target_languages,
        // "sourceLanguage": source_lang,
        "externalReference": text, // set by us, used as identifier
        "sourceObject": window.location.href,
      },
      success: function(result) {
        $.ajax({
          type: "POST",
          url: "./@@translate-text",
          tryCount : 0,
          retryLimit : 20,
          data: {
            "from_annot": result.externalRefId,
          },
          success: function(translation) {
            if (translation) {
              location.reload();
            }
            else {
              this.tryCount++;
              if (this.tryCount <= this.retryLimit) {
                //try again
                $.ajax(this);
                return;
              }
              return;
            }
          },
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout') {
              this.tryCount++;
              if (this.tryCount <= this.retryLimit) {
                //try again
                $.ajax(this);
                return;
              }
              return;
            }
            if (xhr.status == 500) {
              //handle error
            } else {
              //handle error
            }
          }});
      },
      error: function(result) {
        alert('error');
      }
    });
  };

  var editTranslation = function(e) {
    //e.preventDefault();
    var $cell = $(this).parents('td.translatable');

    var $text_div = $('.tr-text', $cell);
    var old_translation = $('.transl', $text_div).text();
    var orig_text = $('.text', $text_div).text();

    $('#transl-original-text').text(orig_text);
    $('#transl-old-translation').text(old_translation);

    $('#form-edit-translation')[0].elements['new_transl'].value = old_translation;

  };

  var submitTranslation = function(e) {
    e.preventDefault();

    var orig_text = $('#transl-original-text').text();
    var $form = $('#form-edit-translation');
    var translation = $form[0].elements['new_transl'].value;

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

  window.addTranslateClickHandlers = function() {
    // $(".autoTransl").on("click", autoTranslation);
    $('.editTransl').on("click", editTranslation);
    $('.submitTransl').on("click", submitTranslation);

    // todo: toggle clickability of buttons?
    $('.btn-translate-orig').on("click", toggleTranslations);
    $('.btn-translate-transl').on("click", toggleTranslations);
  };

  addTranslateClickHandlers();

});
