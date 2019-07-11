(function($){

  $.fn.isInViewport = function() {
    var elementTop = $(this).offset().top;
    var elementBottom = elementTop + $(this).outerHeight();

    var viewportTop = $(window).scrollTop();
    var viewportBottom = viewportTop + $(window).height();

    return elementBottom > viewportTop && elementTop < viewportBottom;
  };

  function setCommentCookie() {
    var token = 's--Plone' + window.location.pathname.split('/').slice(0,-1).join('-');
    document.cookie = token + "=" + Date.now() + ";path=/";
  }

  function colorComments() {
    // setup colored chat depending on user
    colorPalette = {
      'light': ["lightgreen", "lightblue", "lightgoldenrodyellow", "lightgrey"],
      'dark': ["darkgreen", "darkblue", "darkmagenta", "darkred"]
    }

    usernames = {
      'light': [],
      'dark': []
    };

    $('.comment-name').each(function(){
      var groupId = $(this).attr('group-id');
      var username = $(this).text();

      if (usernames[groupId].indexOf(username) === -1) {
        usernames[groupId].push(username);
      }

    });

    $('.comms').each(function(){
      var $commentName = $(this).find('.comment-name');
      var commenter = $commentName.text();
      var groupId = $commentName.attr('group-id');
      var colorP = colorPalette[groupId];

      indx = usernames[groupId].indexOf(commenter);
      color = colorP[indx % colorP.length];

      $comment = $(this).find('.comment');
      $comment.css('background-color', color);
      if (groupId === 'light'){
        $comment.css('color', 'black');
      }
    });
  }

  function loadComments($el) {
    var qid = $el.data('question-id');
    var threadId = $el.data('thread-id');
    var url = './@@ast-comments?q=' + qid + '&thread_id=' + threadId;
    $.get(url, function(text){
      //console.log('getting comments from url', url);
      $el.html(text);
      colorComments();
    });
  }

  function setupDeleteComments($el) {
    $el.find('.comms .comm-del').each(function(){
      var $this = $(this);
      clickEventExists = $this.data('click-event-setup');
      if(clickEventExists === 'true'){
        return;
      }
      $this.data('click-event-setup', 'true');
      //console.log("setup delete comments");

      $this.on('click', function(){
        var $this = $(this);
        var $comel = $('.comments', $this.closest('.right'));
        var commentName = $this.siblings('.comm-crtr').find('.comment-name').text();
        var commentTime = $this.siblings('.comm-crtr').find('.comment-time').text();
        var text = $this.siblings('.comment').text();
        var qid = $el.data('question-id');
        var threadId = $el.data('thread-id');

        if (confirm("Are you sure you want to delete the comment '" + text + "'?")) {
          var url = './@@del_comment';
          var data = {
            comm_name: commentName,
            comm_time: commentTime,
            text: text,
            q: qid,
            thread_id: threadId,
          };
          $.post(url, data, function(text){
            setCommentCookie();
            $comel.html(text);
            colorComments();
          });
        }
      });
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
        setCommentCookie();
        $comel.html(text);
        $textarea.val('');
        colorComments();
      });
      // console.log(qid, text);
      return false;
    });
  }

  function setupToggleComments() {
    var $discTl = $('.right.disc-tl')
    var $discEc = $('.right.disc-ec')
    var existsDiscTl = $discTl.length
    var existsDiscEc = $discEc.length

    $('.comm-hide').click(function(){
      $(this).closest('.right').addClass('inactive');
    });

    $('.right.discussion .comments').click(function(){
      $thisComm = $(this).closest('.right');

      if($thisComm.hasClass('inactive')){
        $thisComm.toggleClass('inactive');
      }
    });
  }

  function setupDisableAssessmentForms(){
    // used in edit assessment form
    // add the disabled attribute for select/textarea elements
    // if the question type does not match the process phase
    $('#comp-national-descriptor div.subform.disabled div.left')
      .find('textarea').each(function(){
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

  function setupFormSelectOptions() {
    // used in edit assessment form
    // override plone's default 'No value' option with '-'
    $('#comp-national-descriptor div.subform div.left div.assessment-form-input')
      .find("option:contains('No value'), span.select2-chosen:contains('No value')").each(function(){
        $(this).text('-');
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

  function adjustInfoboxPosition() {
    var $repNavToggle = $('#report-nav-toggle');
    var $repNav = $('.report-nav.sticky');
    var $infobox = $('#assessment-edit-infobox');
    var infoboxLength = $infobox.children().length;
    var $ff = $('.form-right-side.fixed-save-btn');

    if (infoboxLength > 0 && $repNav.length){
      $repNav.addClass('has-infobox');
      $infobox.show().css('display', 'inline-block');
      var leftPos = $repNavToggle.position().left - 16;

      if ($ff.length) leftPos = $ff.position().left;

      leftPos = leftPos - $infobox.width();
      $infobox.css('left', leftPos + 'px');
    }
    else {
      $repNav.removeClass('has-infobox');
      $infobox.hide();
    }
  }

  function setupAssessmentInfobox() {
    // add the infobox to the top sticky bar
    // the infobox will show all ges components/targets with 'Not relevant' option selected
    function _addGescompsToInfobox() {
      var gesComps = [];
      var $allQuestions = $('<div>');
      var $infobox = $('div#assessment-edit-infobox');
      var message = "'Not relevant' option selected for the following questions:";
      $infobox.empty();

      $('.subform .left select option:selected').each(function(){
        var value = $(this).text();
        var _id = $(this).parent().attr('id').split('_').slice(-2);
        var questionId = _id[0];
        var _idGescomp = _id[1];

        if (_idGescomp.match('[^a-zA-Z]')) _idGescomp = _idGescomp.split('-').join('.');

        if(value == 'Not relevant') {
          $allQuestions.append($("<span>").addClass('infobox-popover')
            .append(questionId + ": " + _idGescomp));

          if (gesComps.indexOf(_idGescomp) === -1) gesComps.push(_idGescomp);
        }
      });

      gesComps.forEach(function(value, index, array) {
        $infobox.append($('<span>').attr('class', 'info-item').append(value)
        );
      });

      $infobox.attr('class', 'help-popover')
          .attr('data-trigger', 'hover')
          .attr('data-html', 'true')
          .attr('data-placement', 'bottom')
          .attr('data-content', $allQuestions.html())
          .attr('data-original-title', message).popover();

      if(gesComps.length === 0) {
        $infobox.hide();
        return;
      }

      $infobox.append($('<span>').attr('class', 'fa fa-exclamation')
        .css({'font-size': '26px', 'float': 'right', 'display': 'block'})
      );
    }
    _addGescompsToInfobox();

    $('select').change(function(){
      _addGescompsToInfobox();
      adjustInfoboxPosition();
    });
  }

  $(document).ready(function() {
    setCommentCookie();
    setupCommentsListing();
    setupPostComments();
    setupToggleComments();
    setupDisableAssessmentForms();
    setupFormSelectOptions();
    setupUnloadWarning();
    setupAssessmentInfobox();

    // When hovering over the comments section add delete comment event for each comment
    $('.subform .right .comments').mouseenter(
      function(){
        setupDeleteComments($(this));
      }
    );

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

    $sfw.find('#form-buttons-save').addClass('btn-success');
    // Button to translate targets only displayed for art10
    var $btnTranslate = $sfw.find('#form-buttons-translate');
    $btnTranslate.addClass('btn-secondary');
    if(window.location.pathname.indexOf('art10') == -1){
      $btnTranslate.css('display', 'none');
    }

    $win.scroll(function() {
      scroll = $win.scrollTop();
      var fixElement = (scroll + space < btnPos) && (scroll >= rnOffset);
      $sfw.toggleClass('fixed-save-btn', fixElement);
      adjustInfoboxPosition();
    });

  });

}(jQuery));
