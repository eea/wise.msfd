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
      console.log('getting comments from url', url);
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

      var qid = $comel.data('question-id');
      var text = $('textarea', $btn.closest('.textline')).val();

      var url = './@@add_comment';
      $.post(url, {text:text, q: qid}, function(text){
        $comel.html(text);
      });
      // console.log(qid, text);
      return false;
    });
  }

  $(document).ready(function() {
    setupCommentsListing();
    setupPostComments();

    // set comment section height for overflow
    var $sf = $('.subform');
    $sf.each(function() {
      var $this = $(this);
      var $com = $this.find('.right');
      var formHeight = $this.find('.left').height();

      $com.height(formHeight);
    });

  });

}(jQuery));
