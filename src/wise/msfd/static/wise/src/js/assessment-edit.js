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
    var url = './@@ast-comments?q=' + qid;
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
      var text = $textarea.val();

      var url = './@@add_comment';
      $.post(url, {text:text, q: qid}, function(text){
        $comel.html(text);
        $textarea.val('');
      });
      // console.log(qid, text);
      return false;
    });
  }

  $(document).ready(function() {
    setupCommentsListing();
    setupPostComments();

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
    var btnPos = $sfw.offset().top;
    var scroll, space;

    $sfw.find('.btn').addClass('btn-primary btn-lg');
    space = $win.height() - $sfw.height() * 2;

    $win.scroll(function() {
      scroll = $win.scrollTop();

      if (scroll + space < btnPos) {
        $sfw.addClass('fixed-save-form');
      } else {
        $sfw.removeClass('fixed-save-form');
      }
    });

  });

}(jQuery));
