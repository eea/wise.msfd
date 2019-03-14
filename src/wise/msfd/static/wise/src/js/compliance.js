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
  // TODO: please explain what this does and why it's needed
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
    // Because of the way the <th> cells are positioned absolute, to be able to
    // keep them fixed, they are "disconnected" from the regular box sizing
    // layout algorithm. For this reason we have to recompute their height (to
    // make either the <td> or the <th> match same height
    this.each(function() {

      $("th", this).each(function() {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());

        $th.height(cells_max_height);
      });

    });
  };

  function mergeCellsInRow(row, limits) {
    // join adjacent cells with identical text

    var sets = [];

    // group cells by similarity
    $('td', row).each(function(ix) {
      if ((sets.length == 0) || limits.includes(ix)) {   // start of processing
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

    // merge cells that are duplicated
    $(sets).each(function(){
      if (this.length > 1) {
        var colspan = this.length;
        $(this[0]).attr('colspan', colspan).addClass('merged');
        $(this.slice(1)).each(function(){
          $(this).remove();
        });
      }
    });

    // compute new group limits
    if ($(row).hasClass('group')) {
      limits = [];
      $(sets).each(function() {
        var l = this.length;
        if (limits.length) {
          l += limits[limits.length - 1];
        }
        limits.push(l);
      });
    }

    // apply special class to group end cells
    var cursor = 0;
    $('td', row).each(function(iy) {
      var c = parseInt($(this).attr('colspan') || '1');
      cursor += c;
      if (limits.includes(cursor)) {
        $(this).addClass('endgroup');
      }
    });
    return limits;
  }

  $.fn.simplifyTable = function simplifyTable(){
    var $table = $(this);

    if (!$table.data('original')) {
      $table.data('original', $table.html());
    }

    $groups = $('tr', this);
    var limits = [];
    $groups.each(function(){
      limits = mergeCellsInRow(this, limits);
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

      $(this).fixTableHeaderAndCellsHeight();

      setupTranslateClickHandlers();
    }
    setupReadMoreModal();
    setupTranslateClickHandlers();
  };

  /* Used in report data table create a 'read more' modal if the cell content
   * is too long
   */
  function setupReadMoreModal() {
    var $table = $('.table-report');
    var $td = $table.find('td');
    var $modalContent = $('.modal-content-wrapper');
    var maxchars = 500;
    var seperator = '...';

    $td.each(function() {
      var $this = $(this);
      var $tw = $this.find('.tr');

      $tw.each(function() {
        var $thw = $(this);
        var $text = $thw.find('.text-trans');
        var $si = $('<span class="short-intro"/>');

        if ($text.text().length > (maxchars - seperator.length)) {
          $this.addClass('read-more-wrapper');
          $si.insertBefore($text);

          var $intro = $thw.children('.short-intro');
          if ($thw.find('.short-intro').length > 1) {
            $intro.eq(0).remove();
          }
          $intro.text($text.text().substr(0, maxchars-seperator.length) + seperator);

          $this.find('.read-more-btn').click(function() {
            $this.find('.active').children('.text-trans').clone().appendTo($modalContent);
          });
        } else {
          $this.removeClass('read-more-wrapper');
        }
      });

    });

    $('.btn-close-modal').click(function() {
      $modalContent.empty();
    });

    $table.fixTableHeaderAndCellsHeight();
  }

  function setupReportNavigation() {
    // This is a menu that is triggered from a button. When scrolling down, it
    // sticks to the top. Allows navigation between articles/years
    var $reportnav = $('#report-data-navigation');
    $('button', $reportnav).on('click', function() {
      $('.nav-body', $reportnav).toggle();
      $(this).children().toggleClass('fa-bars fa-times');
      return false;
    });
    $('.nav-body', $reportnav).hide();

    // sticky report data navigation
    var $rn = $('.report-nav');
    var $title = $rn.closest('#report-data-navigation').siblings('.report-title');

    if ($rn.length > 0) {
      var stickyOffset = $rn.offset().top;

      $(window).scroll(function() {
        var scroll = $(window).scrollTop();

        if (scroll >= stickyOffset) {
          $rn.addClass('sticky').removeClass('fixed');
          $title.addClass('fixed-title');
        } else {
          $rn.removeClass('sticky').addClass('fixed');
          $title.removeClass('fixed-title');
        }
      });
    }
  }

  function setupTableScrolling() {
    // When dealing with a really wide table, with wide cells, we want to keep
    // the text relatively narrow, but always keep in view that cell content
    var $ot = $('.overflow-table table');

    $ot.each(function() {
      var $tw = $(this);
      var $td = $tw.find('td');

      if (!$td.length) { return; }

      // get table header cell right position
      var $th = $tw.find('th');
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
                tdText.removeClass('td-scrolled');
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
    });
  }

  // check if element is in viewport
  $.fn.isInViewport = function() {
    var elementTop = $(this).offset().top;
    var elementBottom = elementTop + $(this).height();

    var viewportTop = $(window).scrollTop();
    var viewportBottom = viewportTop + $(window).height();

    return elementBottom > viewportTop && elementTop < viewportBottom;
  };

  function addCustomScroll() {
    var $cs = $('<div class="scroll-wrapper">' +
      '<i class="fa fa-table"></i>' +
      '<div class="top-scroll">' +
        '<div class="top-scroll-inner"></div>' +
      '</div>' +
    '</div>');

    $cs.insertAfter($('.overflow-table').find('.inner'));
  }

  function setupCustomScroll() {
    // A fixed scrollbar at the bottom of the window for tables

    var $ot = $('.overflow-table');
    var $win = $(window);

    $ot.each(function() {
      var $t = $(this);
      var topScroll = $('.top-scroll', $t.parent());
      var topScrollInner = topScroll.find('.top-scroll-inner');
      var tableScroll = $('.inner', $t.parent());
      var tableWidth = $('.table-report', $t.parent()).width();
      var tableHeaderWidth = $('th', $t.parent()).width();
      var tableAndHeaderWidth = tableWidth + tableHeaderWidth;
      var customScroll = $('.scroll-wrapper', $t.parent());

      topScrollInner.width(tableWidth);

      topScroll.on('scroll', function() {
        tableScroll.scrollLeft($(this).scrollLeft());
      });

      tableScroll.on('scroll', function() {
        topScroll.scrollLeft($(this).scrollLeft());
      });

      if (tableAndHeaderWidth > $t.width()) {
        $win.on('resize scroll', function() {
          var scroll = $win.scrollTop();

          if ($t.isInViewport()) {
            customScroll.addClass('fixed-scroll');
          } else {
            customScroll.removeClass('fixed-scroll');
          }

          // hide custom scrollbar when it reaches the bottom of the table
          if (scroll >= $t.offset().top + $t.outerHeight() - window.innerHeight) {
            customScroll.hide();
          } else {
            customScroll.show();
          }
        });
      }
    });
  }

  function addFixedTable() {
    var $ot = $('.overflow-table');
    var $table = $ot.find('table');
    var $cb = $('<input type="checkbox" class="fix-row"/>');
    var $ft = $(
      '<div class="fixed-table-wrapper">' +
        '<div class="fixed-table-inner">' +
          '<table class="table table-bordered table-striped fixed-table">' +
          '</table>' +
        '</div>' +
      '</div>'
    );

    $table.find('th').append($cb);
    $ft.insertBefore($ot.find('.inner'));
  }

  function setupFixedTableRows() {
    // Allows report table rows to be fixed while scrolling
    var $ot = $('.overflow-table');
    var $fixedTable = $('.fixed-table-wrapper');

    $ot.each(function() {
      var $t = $(this);
      var $th = $('th', $t.parent());
      var tableW = $('.table-report', $t.parent()).width();
      var tableScroll = $('.inner', $t.parent());
      var fixedTableInner = $('.fixed-table-inner', $t.parent());

      function toggleSyncScrolls(onoff) {
        function f1 () {
          tableScroll.scrollLeft($(this).scrollLeft());
        }
        function f2 () {
          fixedTableInner.scrollLeft($(this).scrollLeft());
        }
        if (onoff) {
          fixedTableInner.on('scroll', f1);
          tableScroll.on('scroll', f2);
        } else {
          fixedTableInner.off('scroll', f1);
          tableScroll.off('scroll', f2);
        }
      }
      toggleSyncScrolls(true);

      $th.each(function(i) {
        var val = "cb" + i++;
        var checkBox = $(this).find('.fix-row');
        checkBox.val(val);
      });

      var checkBox = $t.find('.fix-row');
      checkBox.change(function() {
        var $this = $(this);
        var value = $this.val();
        var table = $this.closest('.overflow-table').find('.fixed-table');
        var tableWrapper = $this.closest('.overflow-table').find('.fixed-table-wrapper');
        $('.fixed-table').width(tableW);

        if ($this.is(':checked')) {
          tableWrapper.addClass('sticky-table');

          // clone table row, but keep the width of the original table cells
          var target = $this.closest('tr');
          var target_children = target.children('td');
          var clone = target.clone();
          clone.children('td').width(function(i,val) {
            return target_children.eq(i).outerWidth();
          });
          clone.appendTo(table).attr('data-row', value);

          $t.find('.table').fixTableHeaderAndCellsHeight();
          // setupTableScrolling();
        } else {
          $fixedTable.find('tr[data-row="' + value + '"]').slideUp('fast', function() {
            $(this).remove();
          });

          if (table.find('tr').length === 1) {
            tableWrapper.removeClass('sticky-table');
          }
        }

        var $cb = $fixedTable.find('.fix-row');
        $cb.change(function() {
          var $this = $(this);
          var value = $this.val();

          if ($this.closest('tr').siblings().length === 0) {
            $this.closest('.fixed-table-wrapper').removeClass('sticky-table');
          }

          $this.closest('tr').remove();
          $('.fix-row[value="' + value + '"]').prop('checked', false);
        });

        toggleSyncScrolls(false);
        fixedTableInner.scrollLeft(tableScroll.scrollLeft());
        toggleSyncScrolls(true);

      });

    });

    $(window).on('resize scroll', function() {
      if ($('.report-nav.sticky').length > 0) {
        $fixedTable.css('top', '58px');
      } else {
        $fixedTable.css('top', '0');
      }
    });
  }

  function setupResponsiveness() {
    // fire resize event after the browser window resizing it's completed
    var resizeTimer;
    $(window).resize(function() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(doneResizing, 500);
    });

    function doneResizing() {
      $('.table-report').fixTableHeaderHeight();
    }

    if (window.matchMedia("(max-width: 768px)").matches) {
      $(".overflow-table h5").width( $(".overflow-table table").width() );
    }

    var $td = $('.overflow-table table td');
    $td.children('div').wrapInner('<div class="td-content" />');
  }

  function setupSimplifiedTables() {
    $('.simplify-form').next().find('.table-report').each(function(){
      $(this).simplifyTable();
    });

    $('.simplify-form button').on('click', function(){
      var onoff = $(this).attr('aria-pressed') == 'true';
      $p = $(this).parent().next();
      $('.table-report', $p).toggleTable(!onoff);
      setupCustomScroll();
      setupFixedTableRows();
    });
  }

  $(document).ready(function($){
    initStyling();
    setupSelects2();
    setupReportNavigation();
    // setupTableScrolling();
    setupReadMoreModal();
    setupResponsiveness();
    addCustomScroll();
    addFixedTable();

    $(window).on('load', function() {
      setupSimplifiedTables();
      setupCustomScroll();
      setupFixedTableRows();
    });
  });
}(window, document, $));
