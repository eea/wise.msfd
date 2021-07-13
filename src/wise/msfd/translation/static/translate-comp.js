(function(window, document, $){

  var setupTranslationsInReportPage = function () {

    /*
     * Triggered by translation edit btn. Sets proper text in modal edit dialog
     */
    function setupEditTranslationDialog () {

      var $original = $('#transl-original-text');
      var $old = $('#transl-old-translation');

      var $cell = $(this).parents('td.translatable');

      var $trText = $('.tr-text', $cell);
      var old_translation = $trText.data('translation');
      var orig_text = $trText.data('original');

      $original.text(orig_text);
      $old.text(old_translation);

      var $textarea = $('#form-edit-translation #new_transl');
      $textarea.val(old_translation.trim());

      /*
       * For regional descriptors update the Edit translation form's source language
       * with the cell's languge
       */
      var source_lang = $cell.attr('source-lang');
      var $form = $('#form-edit-translation');
      $form.children('input').attr('value', source_lang);
    };

    /*
     * Handles clicking on save translation in the edit translation dialog
     */
    function handleTranslationSave (e) {

      // inline editing in report data view page
      e.preventDefault();

      var $original = $('#transl-original-text');
      var $old = $('#transl-old-translation');

      var orig_text = $original.text().trim();
      var $form = $('#form-edit-translation');
      var translation = $("#new_transl", $form).val();
      var url = $('.form-group').attr('portal_url') + '/@@edit-translation';
      var language = $form.children('input').attr('value');

      $.ajax({
        form: $form,
        type: 'POST',
        url: url,
        dataType: 'json',
        data: {
          'original': orig_text,
          'tr-new': translation,
          'language': language,
        },
        success: function (result) {
          location.reload();
        },
        error: function (result) {
          alert('ERROR saving translation!');
        }
      });

      $('.submitTransl')
        .attr('disabled', true)
        .attr('value', 'Please wait...')
      ;
    };


    /*
     * Setup the translations in the report data view screens
     */
    function toggleTranslations () {
      //
      $(this).toggleClass('active');
      $(this).siblings('.btn-translate').toggleClass('active');

      var $langToolbar = $(this).parents('.lang-toolbar');
      var $trText = $langToolbar.siblings('.tr-text');
      $langToolbar.toggleClass('blue green');

      // var $cell = $(this).parents('td.translatable');
      // $('.text', $cell).toggleClass('blue');
      // $('.transl', $cell).toggleClass('green');

      if ($langToolbar.hasClass('blue')) {
        $trText.html($trText.data('original'));
      } else if ($langToolbar.hasClass('green'))  {
        $trText.html($trText.data('translation'));
      }      

      setupReadMoreModal();

      // fix height of <th> on this row
      var $th = $(this).parents('tr').find('th').each(function(){
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());

        $th.height(cells_max_height);
      });

      // $(this).parents('.table-report').fixTableHeaderAndCellsHeight();
      // $th.fixTableHeaderHeight();

      // fix height of lang-toolbar on this row
      // $(this).parents('tr').find('.lang-toolbar').each(function(){
      //   var $this = $(this);
      //   $this.css('height', $this.parents('tr').height());
      // });
      
    };

    function setupUITranslatedCells() {
      $('.lang-toolbar').each(function(){
        var $this = $(this),
          $p = $this.parent();

        var $c = $this
          // .css('height', h)
          .children()
          .hide();
        ;
        console.log();

        function inhover(){
          var p = $p.position();
          $this
            .css({
              width: 'initial',
              height: '2.7em',
              position: 'absolute',
              float: 'none',
              top: p.top,
              left: p.left
            })
            .children()
            .show()
          ;
        }
        function outhover() {
          $this
            .css({
              width: '4px',
              float: 'left',
              position: 'initial',
              height: '10px'
            })
            .children()
            .hide()
          ;
        }

        $this.hover(inhover, outhover);
      });
    }

    function autoTranslation() {
      var $form = $(".form-refresh-translation");
      var $cell = $(this).parents('td.translatable');
      // var text = $('.tr-text', $cell).text();
      var text = $('.tr-text', $cell).attr("data-original");

      /*
       * For regional descriptors
       * update the form's language with the cell's language
       */
      var source_lang = $cell.attr('source-lang');
      $form.children("input[name=language]").attr("value", source_lang);

      $form.find('textarea').val(text);
      $form.submit();
    }
    
    window.setupTranslateClickHandlers = function () {
      $(".autoTransl").on("click", autoTranslation);    
      // todo: toggle clickability of buttons?
      setupUITranslatedCells();

      $('.editTransl').on("click", setupEditTranslationDialog);
      $('.submitTransl').on("click", handleTranslationSave);

      $('.lang-orig').on("click", toggleTranslations);
      $('.lang-transl').on("click", toggleTranslations);
    };

    setupTranslateClickHandlers();

  };

  var setupTranslationsInOverviewPage = function () {
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

    $("a.auto-translate").click(function() {
      $this = $(this);
      var url = "/marine/translate-text";
      var data = {};
      data['language'] = $this.attr('selectedlang');
      data['text'] = $this.parents('tr').children('td')[0].outerText;

      $this.children('i').removeClass('glyphicon-refresh');
      $this.children('i').addClass('glyphicon-ok');

      debugger;

      $.ajax({
        type: "POST",
        url: url,
        data: data,
        success: function(data)
        {}
      });

      return false;
    });
  };

  $(document).ready(function(){
    var onReport = $('.report-page-view ').length;

    if (onReport) {
      setupTranslationsInReportPage();
    } else {
      setupTranslationsInOverviewPage();
    }
  });

})(window, document, jQuery);
