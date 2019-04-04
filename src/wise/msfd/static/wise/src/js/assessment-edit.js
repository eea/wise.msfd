(function($){

  $.fn.isInViewport = function() {
    var elementTop = $(this).offset().top;
    var elementBottom = elementTop + $(this).outerHeight();

    var viewportTop = $(window).scrollTop();
    var viewportBottom = viewportTop + $(window).height();

    return elementBottom > viewportTop && elementTop < viewportBottom;
  };

  function loadComments($el) {
    var qid = $el.data('question-id');
    var threadId = $el.data('thread-id');
    var url = './@@ast-comments?q=' + qid + '&thread_id=' + threadId;
    $.get(url, function(text){
      // console.log('getting comments from url', url);
      $el.html(text);
    });
  }

  function setupCommentsListing() {
    $(window).on('resize scroll', function() {
      $('.subform .right .comments').each(function(){
        var $n = $(this);

        if ($n.data('comments-loaded') === 'true') {
          return;
        }
        if ($n.isInViewport()) {
          $n.data('comments-loaded', 'true');
          loadComments($n);
        }
      });
    });
  }

  function setupPostComments() {
    $('.subform .right .textline button').on('click', function() {
      var $btn = $(this);
      var $comel = $('.comments', $btn.closest('.right'));
      var $textarea = $('textarea', $btn.closest('.textline'));

      var qid = $comel.data('question-id');
      var threadId = $comel.data('thread-id');
      var text = $textarea.val();

      if (!text) return false;

      var url = './@@add_comment';
      var data = {
        text:text,
        q: qid,
        thread_id: threadId
      };
      $.post(url, data, function(text){
        $comel.html(text);
        $textarea.val('');
      });
      // console.log(qid, text);
      return false;
    });
  }


  function setupDisableAssessmentForms(){
    // used in edit assessment form
    // add the disabled attribute for select/textarea elements
    // if the question type does not match the process phase
    $('#comp-national-descriptor div.subform.disabled div.left')
      .find('select, textarea').each(function(){
        $(this).attr('disabled', true);
    });

    // used in edit assessment form
    // remove the disabled attribute when submitting the form
    // data from disabled attributes is not submitted
    $('.kssattr-formname-edit-assessment-data-2018').submit(function(){
      $(':disabled').each(function(){
        $(this).removeAttr('disabled');
      });
    });
  }

  function setupUnloadWarning() {
    // National descriptor edit assessment data
    // Warn user before leaving the page with unsaved changes
    var submitted = false;
    var modified = false;
    var $nd = $('#comp-national-descriptor');

    $('#comp-national-descriptor form').submit(function() {
      submitted = true;
    });

    $nd.on('change', 'input, textarea, select', function(e) {
      modified = true;
    });

    $(window).bind('beforeunload', function() {
      if (modified && !submitted) {
        // most browsers ignores custom messages,
        // in that case the browser default message will be used
        return "You have unsaved changes. Do you want to leave this page?";
      }
    });

    var $select = $nd.find('.select2-container');
    var $textarea = $nd.find('textarea');
    $select.closest('.fields-container-row').addClass('flex-select');
    $textarea.closest('.fields-container-row').addClass('flex-textarea');
  }

  $(document).ready(function() {
    setupCommentsListing();
    setupPostComments();
    setupDisableAssessmentForms();
    setupUnloadWarning();

    var $win = $(window);

    // set comment section height for overflow
    var $sf = $('.subform');
    $sf.each(function() {
      var $this = $(this);
      var $com = $this.find('.right');
      var formHeight = $this.find('.left').innerHeight();

      $com.innerHeight(formHeight);

      var resizeTimer;
      $win.resize(function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function(){
          $com = $this.find('.right');
          formHeight = $this.find('.left').innerHeight();
          $com.innerHeight(formHeight);
        }, 100)
      });
    });

    // sticky save button
    var $sfw = $('.form-right-side');
    var $rn = $('.report-nav');
    var btnPos = 0;
    var $rnOffset = 0;
    var scroll, space;

    if ($sfw.offset()) btnPos = $sfw.offset().top;
    if ($rn.length > 0) rnOffset = $rn.offset().top;

    space = $win.height() - $sfw.height() * 2;

    $sfw.find('.btn').addClass('btn-success');
    $win.scroll(function() {
      scroll = $win.scrollTop();
      var fixElement = (scroll + space < btnPos) && (scroll >= rnOffset);
      $sfw.toggleClass('fixed-save-btn', fixElement);
    });

  });

}(jQuery));
