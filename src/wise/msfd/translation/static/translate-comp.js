$(document).ready(function () {

  var $original = $('#transl-original-text');
  var $old = $('#transl-old-translation');

  var reportTranslation = function () {

    var editTranslation = function (e) {
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
    
    // console.log("reportTranslation");
    
    var submitTranslation = function (e) {

      // inline editing in report data view page
      e.preventDefault();

      var orig_text = $original.text();
      var $form = $('#form-edit-translation');
      var translation = $("#new_transl", $form).val();
      var url = $('.form-group').attr('portal_url') + '/@@edit-translation';
      console.log(':', translation);

      $.ajax({
        form: $form,
        type: 'POST',
        url: url,
        dataType: 'json',
        data: {
          'original': orig_text,
          'tr-new': translation,
        },
        success: function (result) {
          location.reload();

        },
        error: function (result) {
          alert('ERROR saving translation!');
        }
      });
    };

    var toggleTranslations = function (e) {
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

      var $th = $(this).parents('tr').find('th');
      // $tr.fixTableHeaderHeight();

      $th.each(function () {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());

        $th.height(cells_max_height);
      });
    };

    window.setupTranslateClickHandlers = function () {
      // $(".autoTransl").on("click", autoTranslation);
      // todo: toggle clickability of buttons?      
      
      $('.editTransl').on("click", editTranslation);
      $('.submitTransl').on("click", submitTranslation);
      $('.btn-translate-orig').on("click", toggleTranslations);
      $('.btn-translate-transl').on("click", toggleTranslations);
    };

    setupTranslateClickHandlers();

  };

  var setupOverviewTranslation = function () {
    var $form = $('#form-edit-translation');
    var $modal = $('#edit-translation');

    $modal.on('show.bs.modal', function (event) {
      $form.off('submit');
      // setup the modal to show proper values
      var $btn = $(event.relatedTarget);
      var cells = $btn.parent().parent().children();

      var original = $(cells[0]).text();
      var translated = $(cells[1]).text();

      $('#tr-original').text(original);   // show original text
      $('textarea[name="original"]', $form).val(original);   // form input

      $('#tr-new').val(translated);    // textarea for new translation

      $('#tr-current').text(translated);    // show current translation    
      $form.on('submit', function () {
        var url = $form.attr('action');
        var data = {};

        $('textarea,input', $form).each(function () {
          var name = $(this).attr('name');
          if (!name) return;
          data[name] = $(this).val();
        });

        // $.post(url, data, function(resp) {
        //   $modal.modal('hide');
        //   var $cell = $(cells[1]);
        //   $cell.hide();
        //   $cell.text(resp['text']);
        //   $cell.fadeIn(1000);
        // });


        $.ajax({
          form: $form,
          type: 'POST',
          url: url,
          dataType: 'json',
          data: data,
          success: function (result) {
            location.reload(); // reload page from the server, ignoring cache
          },
          error: function (result) {
            alert('ERROR saving translation!');
          }
        });

        return false;
      });
    });
  };

  var onReport = $('.report-page-view ').length;

  if (onReport) {
    reportTranslation();
  }
  else {
    setupOverviewTranslation();
  }
});
