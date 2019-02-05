if (!Array.prototype.last){
  Array.prototype.last = function(){
    return this[this.length - 1];
  };
};

(function(window, document, $){

  var selectorFormContainer = ".wise-search-form-container";
  var exceptVal = ["all", "none", "invert", "apply"];
  /*
   * SELECT2 functions
   * */
  function setupSelects2(selector){
    var forbiddenIDs = [];
    var selectorFormCont = selector || selectorFormContainer;

    $(selectorFormCont + " select").each(function(ind, selectElement) {
      var selectedElementID = $(selectElement).attr("id");
      if(forbiddenIDs.indexOf(selectedElementID) !== -1){
        return false;
      }

      $(selectElement).addClass("js-example-basic-single");
      var lessOptions = $(selectElement).find("option").length < 10;

      var options = {
        placeholder: 'Select an option',
        closeOnSelect: true,
        dropdownAutoWidth : true,
        width: '100%',
        theme: "flat"
      };
      if (lessOptions) options.minimumResultsForSearch = Infinity;

      $(selectElement).select2(options);
    });
  }

  function initStyling(){
    // TODO: is this still needed? I don't think so
    //$("#form-buttons-continue").hide("fast");
    $(".button-field").addClass("btn");

    // mobile hide .toggle-sidebar
    $(".toggle-sidebar").hide();
  }

  $.fn.fixTableHeaderAndCellsHeight = function fixTableHeaderAndCellsHeight() {
    // because the <th> are position: absolute, they don't get the height of
    // the <td> cells, and the other way around.
    this.each(function() {

      $("th", this).each(function() {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());
        var height = Math.max($th.height(), cells_max_height);

        $th.height(height);

        if ($th.height() > cells_max_height) {
          $next.height($th.height());
        }
      });
    });
  };

  $.fn.fixTableHeaderHeight = function fixTableHeaderHeight() {
    this.each(function() {

      $("th", this).each(function() {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());

        $th.height(cells_max_height);
      });

    });
  };

  $.fn.simplifyTable = function simplifyTable(){
    var $table = $(this);

    if (!$table.data('original')) {
      $table.data('original', $table.html());
    }

    // stretch all cells to the maximum table columns;
    var max = 0;
    var $tr = $('tr', this);
    $tr.each(function(){
      $tds = $('td', this);
      if ($tds.length > max) {
        max = $tds.length;
      }
    });

    $tr.each(function(){
      $tds = $('td', this);
      if ($tds.length) {
        var td = $tds[$tds.length - 1];
        $(td).attr('colspan', max - $tds.length + 1);
      }
    });

    // join adjacent cells with identical text
    $tr.each(function(){
      var sets = [];
      $('td', this).each(function() {
        if (sets.length == 0) {   // start of processing
          sets.push([this]);
        } else {
          var thisText = $(this).text().trim();
          var lastText = $(sets.last().last()).text().trim();

          if ((thisText.length > 0) && (thisText == lastText)) {
            sets.last().push(this);
          } else {
            sets.push([this]);
          }
        }
      });
      $(sets).each(function(){
        if (this.length > 1) {
          var colspan = this.length;
          $(this[0]).attr('colspan', colspan);
          $(this.slice(1)).each(function(){
            $(this).remove();
          });
        }
      });
    });

    $table.fixTableHeaderHeight();
    $table.data('simplified', $table.html());
  };

  $.fn.toggleTable = function toggleTable(onoff) {
    var original = $(this).data('original');
    var simplified = $(this).data('simplified');
    if (onoff) {
      //$(this).simplifyTable();
      $(this).html(simplified);
    } else {
      $(this).hide();
      $(this).empty().html(original);
      $(this).show();

      console.log("done restoring");
      $(this).fixTableHeaderAndCellsHeight();

      //addTranslateClickHandlers();
    }
    readMoreModal();
    // addTranslateClickHandlers();
  };

  // used in report data table
  // create a 'read more' modal
  // if the cell content is too long
  function readMoreModal() {
    var $table = $('.table-report');
    var $td = $table.find('td');
    var maxchars = 500;
    var seperator = '...';

    $td.each(function() {
      var $this = $(this);
      var $text = $this.find('.active').children('.text-trans');
      var $si = $('<span class="short-intro"/>');

      if ($text.text().length > (maxchars - seperator.length)) {
        $this.addClass('read-more-wrapper');
        $si.insertBefore($text);

        var $intro = $this.find('.active').children('.short-intro');

        if ($this.find('.short-intro').length > 1) {
          $intro.eq(0).remove();
        }

        $intro.text($text.text().substr(0, maxchars-seperator.length) + seperator);

        $this.find('.read-more-btn').click(function() {
          $text.clone().appendTo($('.modal-content-wrapper'));
        });
      } else {
        $this.removeClass('read-more-wrapper');
      }
    });

    $('.btn-close').click(function() {
      $('.modal-content-wrapper').empty();
    });

    $table.fixTableHeaderAndCellsHeight();
  }

  function setupReportNavigation() {
    var $reportnav = $('#report-data-navigation');
    $('button', $reportnav).on('click', function() {
      $('.nav-body', $reportnav).toggle();
      return false;
    });
    $('.nav-body', $reportnav).hide();
  }

  function setupTableScrolling() {
    var $td = $('.table-report td');

    if (!$td.length) { return; }

    $td.children('div').wrapInner('<span class="td-content"/>');

    // get table header cell right position
    var $th = $('.table-report th');
    var thRight = $th.position().left + $th.outerWidth();

    $td.each(function() {
      var $this = $(this);
      var scrollTimer;

      $('.report-page-view .overflow-table .inner').scroll(function() {
        clearTimeout(scrollTimer);

        if ($this.attr('colspan') > 1) {
          var tdText = $this.find('.td-content');
          var tdLeft = $this.position().left;
          var tdRight = tdLeft + $this.outerWidth(); // get table cell right position
          var tdTextWidth = $this.find('.td-content').width();
          var thAndCellWidth = tdTextWidth + thRight;

          $this.css('height', $this.outerHeight());

          scrollTimer = setTimeout(function() {
            afterScroll()}, 1);

          if (tdLeft < thRight) {
            tdText.addClass('td-scrolled').css('left', thRight + 5);
          } else {
            $this.css('height', '');
            tdText.removeClass('td-scrolled').addClass('td-content-scrolled');
          }

          if (thAndCellWidth >= tdRight) {
            $this.addClass('td-relative');
          } else {
            $this.removeClass('td-relative');
          }
        }

      });

      function afterScroll() {
        $('.btn-translate').on('click', function() {
          var $btn = $(this);
          var transTextHeight = $btn.closest('.td-content').outerHeight();
          var $td = $btn.closest('td.translatable');
          var $th = $td.siblings('th');
          $td.css({
            'height': transTextHeight,
            'padding': '0'
          });
          $btn.closest('.td-content').css('padding', '8px');
          $th.css('height', transTextHeight);
        });
      }
    });
  }

  // used in edit assessment form
  // add the disabled attribute for select/textarea elements
  // if the question type does not match the process phase
  function disableAssessmentForms(){
    $('div.subform.compliance-assessment-edit-subform.disabled')
      .find('select, textarea').each(function(){
        $(this).attr('disabled', true);
    });
  }

  $(document).ready(function($){
    initStyling();
    setupSelects2();
    setupReportNavigation();
    setupTableScrolling();
    disableAssessmentForms();
    readMoreModal();

    // used in edit assessment form
    // remove the disabled attribute when submitting the form
    // data from disabled attributes is not submitted
    $('.kssattr-formname-edit-assessment-data-2018').submit(function(){
      $(':disabled').each(function(){
        $(this).removeAttr('disabled');
      });
    });

    if (window.matchMedia("(max-width: 768px)").matches) {
      $(".overflow-table h5").width( $(".overflow-table table").width() );
    }

    //$('.simplify-form').next().find('table').simplifyTable();

    // tibi
    $('.simplify-form').next().find('table').each(function(){
      $(this).simplifyTable();
    });

    // fire resize event after the browser window resizing it's completed
    var resizeTimer;
    $(window).resize(function() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(doneResizing, 500);
    });

    function doneResizing() {
      $('.table-report').fixTableHeaderHeight();
    }

    $('.simplify-form button').on('click', function(){
      var onoff = $(this).attr('aria-pressed') == 'true';
      $p = $(this).parent().next();
      $('table', $p).toggleTable(!onoff);
    });

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

  });
}(window, document, $));
