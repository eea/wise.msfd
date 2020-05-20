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

  function setupTargetsWidth() {
    // Make targets extend on multiple rows when there are many targets
    // and the assessment-data-table is scrollable
    var $tableWrap = $('.table-wrap');
    var $assessmentTable = $('#container-assessment-data-2018 .assessment-data-table');
    if($assessmentTable.width() <= $tableWrap.width()) {
      return
    }

    $('div.gescomp', $tableWrap).css({'display': 'inline-table', 'min-width': 'inherit', 'width': 'inherit'});

    var maxGescompWidth = 0;
    $('div.gescomp', $tableWrap).each(function(){
      var width = $(this).width();
      if (width > maxGescompWidth){
        maxGescompWidth = width;
      }
    });

    $('div.gescomp', $tableWrap).css({'width': maxGescompWidth});

    // $(window).on('resize', adjustTargetsWidth);
  }

  function setupScrollableTargets() {
    // NOT USED
    // create a clone of the assessment data 2018 table and overlap the original table
    // with fixed question and score columns
    $('#container-assessment-data-2018 .table.table-condensed.assessment-data-table')
      .clone(true).appendTo('#container-assessment-data-2018').addClass('clone');

    var $orig = $('.table-wrap .table.table-condensed.assessment-data-table');
    var $clone = $('.table.table-condensed.assessment-data-table.clone');
    var origLength = $orig.find('tr').length;
    var origHeight, cloneHeight;

    for(var i=0; i < origLength; i++){
      var x = $clone.find('tr')[i]
      cloneHeight = $(x).find('.fixed-center').innerHeight();
      origHeight = $($orig.find('tr')[i]).innerHeight();

      if(origHeight > cloneHeight) {
        $(x).css('height', origHeight + 'px');
      }
      else {
        $($orig.find('tr')[i]).css('height', cloneHeight + 'px');
      }
    }
  }

  $.fn.fixTableHeaderAndCellsHeight = function() {
    // because the <th> are position: absolute, they don't get the height of
    // the <td> cells, and the other way around.

    this.each(function() {
      $("th", this).each(function() {
        var $th = $(this);
        var $next = $('td:not(".sub-header")', $th.parent());
        var $subheader = $('td.sub-header', $th.parent())
        var tdHeights = [];

        $next.each(function(){
          var $this = $(this);
          if($this.hasClass('translatable')) {
            var hght = $this.find('.tr-text').height();
            tdHeights.push(hght);
          } else {
            tdHeights.push($this.height());
          }
        });

        var cells_max_height = Math.max.apply(Math, tdHeights);
        var height = Math.max($th.height(), $subheader.height(), cells_max_height);

        $th.height(height);
        $subheader.height(height);
        if ($th.height() > cells_max_height) {
          $next.each(function(){
            $(this).height($th.height())
          });
          //$next.height($th.height());
        }

        $('div', this).css('margin-top', '-4px');

      });
    });

    // $('tr .lang-toolbar', this).each(function() {
    //   console.log('fixing', this);
    //   var $this = $(this);
    //   var height = $this.parents('tr').height();
    //   $this.css('height', height);
    // });

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
        var tdHeights = [];

        $next.each(function(){
          var $this = $(this);
          if($this.hasClass('translatable')) {
            var hght = $this.find('.tr-text').height();
            tdHeights.push(hght);
          } else {
            tdHeights.push($this.height());
          }
        });

        var cells_max_height = Math.max.apply(Math, tdHeights);

        $th.height(cells_max_height);
      });

    });
  };

  function mergeCellsInRow(row, cache) {
    /* This function visually groups and merges cells in table, to optimize
     * for reading information.
     *
     * It joins adjacent cells that have identical text, but uses group
     * definitions to establish "limits" on what it can merge. Finally, those
     * "groups" end cells are marked with special classes, to distinguish them
     * visually.
     */

    var sets = [];

    // get the appropriate limits from the cache, based on the current level
    var limits = [];
    var rowLevel = $(row).data('level');
    rowLevel = (rowLevel != undefined) ? parseInt(rowLevel) : -1;
    $(cache.setlimits).each(function() {
      if (this.level == rowLevel) {
        limits = this.limits;
        return false;
      }
    });
    if (limits.length == 0) {
      limits = cache.setlimits[cache.setlimits.length - 1].limits;
    }

    // group cells by similarity
    $('td', row).each(function(ix) {
      if ((sets.length == 0) || limits.includes(ix)) {
        sets.push([this]);
      } else {
        var thisText = $(this).text().trim();
        var lastText = $(sets.last().last()).text().trim();

        if  (thisText == lastText) {
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
        $(this[0]).attr('colspan', colspan);  // .addClass('merged');
        $(this.slice(1)).each(function(){
          $(this).remove();
        });
      }
    });

    // compute new group limits
    if (rowLevel != -1) {
      limits = [];
      cache.curentLevel = rowLevel;

      $(sets).each(function() {
        var l = this.length;
        if (limits.length) {
          l += limits[limits.length - 1];
        }
        limits.push(l);
      });
      cache.setlimits.push({
        level: cache.curentLevel,
        limits: limits.slice(0)   // makes a copy
      });
    }

    // apply special class to group end cells
    var cursor = 0;
    $('td', row).each(function(iy) {
      var level = cache.curentLevel;
      var l;
      var prevset;

      var c = parseInt($(this).attr('colspan') || '1');
      cursor += c;

      if (limits.includes(cursor)) {
        if (level > 0) {
          // traverse all previous limits to see which major one includes
          // this limit
          for (l=0; l < cache.setlimits.length; l++) {
            prevset = cache.setlimits[l].limits;
            if (prevset.includes(cursor)) {
              level = cache.setlimits[l].level;
              break;
            }
          }
        }
        $(this).addClass('endgroup_' + level);
      }
    });
  }

  $.fn.simplifyTable = function simplifyTable(){
    var $table = $(this);

    if (!$table.data('original')) {
      $table.data('original', $table.html());
    }

    var cache = {
      curentLevel: 0,
      setlimits: [{
        level: -1,
        limits: []
      }]
    };
    $('tr', this).each(function(){
      mergeCellsInRow(this, cache);
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
      //$(this).fixTableHeaderAndCellsHeight();
      setupTranslateClickHandlers();
      //setupReadMoreModal();
    }
    setupReadMoreModal();
    setupTranslateClickHandlers();
  };

  /* Used in report data table create a 'read more' modal if the cell content
   * is too long
   */
  window.setupReadMoreModal = function() {
    var $table = $('.table-report');
    var $modal = $("#read-more-modal");
    var $modalContent = $('.modal-content-wrapper');
    var maxchars = 397;
    var sep = '...';
    var $cells = $table.find('.tr-text');
    $cells.each(function() {
      var t = $(this).text();
      var t_html = $(this).html();

      if (t_html.length > maxchars) {
        $(this).addClass('short');
        var sh = t_html.substr(0, 0.75*maxchars) + sep;
        $(this).html(sh);
        $(this).on('click', function() {
          $modalContent.html(t_html);
          $modal.modal('show');
        });
      };
    })

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
    var $title = $('.report-title');

    if ($rn.length > 0) {
      var stickyOffset = $rn.offset().top;

      $(window).scroll(function() {
        var scroll = $(window).scrollTop();
        var fixElement = scroll >= stickyOffset;
        $rn.toggleClass('sticky', fixElement);
        $title.toggleClass('fixed-title', fixElement);
      });
    }
  }

  function setupTableScrolling() {
    // TODO not used
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

            scrollTimer = setTimeout(afterScroll, 1);

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
            // Tibi: temporarily disabled
            // $('.btn-translate').on('click', function() {
            //   var $btn = $(this);
            //   var transTextHeight = $btn.closest('.td-content').outerHeight();
            //   var $td = $btn.closest('td.translatable');
            //   var $th = $td.siblings('th');
            //   $td.css({
            //     'height': transTextHeight,
            //     'padding': '0'
            //   });
            //   $btn.closest('.td-content').css('padding', '8px');
            //   $th.css('height', transTextHeight);
            // });
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
      var tableWidth = $('.table-report', $t.parent()).outerWidth(includeMargin=true);
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
        '<button title="Clear filters" class="btn btn-primary btn-xs reset-pins">' +
          '<i class="fa fa-times" aria-hidden="true"></i>' +
        '</button>' +
        '<div class="fixed-table-inner">' +
          '<table class="table table-bordered table-striped fixed-table">' +
          '</table>' +
        '</div>' +
      '</div>'
    );

    // Register click event for button to clear all pinned rows for the current table
    $ft.find('button.reset-pins').click(function(){
      $ftw = $(this).closest('.fixed-table-wrapper');
      $ftw.removeClass('sticky-table');
      $ftw.find('tr').remove();

      $innerTable = $ftw.siblings('.inner');
      $innerTable.find('tr input').prop('checked', false);
    });

    if($table.find('td.sub-header').length){
      // Regional descriptors
      $table.find('td.sub-header').append($cb);
    } else {
      // National descriptors
      $table.find('th div').append($cb);
    }

    $ft.insertBefore($ot.find('.inner'));
  }

  $.fn.setupFixedTableRows = function() {
    // Allows report table rows to be fixed while scrolling
    // var $ot = $('.overflow-table');
    var $ot = $(this)
    var $fixedTable = $('.fixed-table-wrapper');

    // The .each is unnecesary, because we always fix only one table
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

      $('.fix-row').each(function(i) {
        var val = "cb" + i++;
        // var checkBox = $(this).find('.fix-row');
        var checkBox = $(this);
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

          //for other tables find the reset button and trigger the click event
          var $parentReportSection = $this.closest('.report-section');
          var $otherReportSections = $parentReportSection.siblings('.report-section');
          $otherReportSections.each(function(){
            $ftw = $(this).find('.fixed-table-wrapper');
            $ftw.find('button.reset-pins').click();
          });

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

    // tibi: temporarily disabled. I don't know what td-content does
    // var $td = $('.overflow-table table td');
    // $td.children('div').wrapInner('<div class="td-content" />');
  }

  function setupSimplifiedTables() {
    $('.simplify-form').next().find('.table-report').each(function(){
      $(this).simplifyTable();
    });

    $('.simplify-form button').on('click', function(){
      var onoff = $(this).attr('aria-pressed') == 'true';
      $p = $(this).parent().next();
      $('.table-report', $p).toggleTable(!onoff);
      $p.setupFixedTableRows();
      setupCustomScroll();
    });
  }

  function regionalDescriptorsGroupTableHeaders() {
    var $headers = $('.first-header');
    if($headers.length === 0){
      return
    }
    var compareText = '';
    var currentText = '';

    compareText = $headers[0].firstElementChild.innerText;

    for (i=1; i < $headers.length; i++) {
      currentText = $headers[i].firstElementChild.innerText;

      if(compareText === currentText) {
          $headers[i].firstElementChild.innerText = '';
          $($headers[i-1]).css('border-bottom', '0px');
      } else {
        compareText = currentText;
      }

      //debugger;
    }
  }

  $(document).ready(function($){

    setupReadMoreModal();
    initStyling();
    setupSelects2();
    setupReportNavigation();
    // setupTableScrolling();
    setupResponsiveness();
    addCustomScroll();
    addFixedTable();
    regionalDescriptorsGroupTableHeaders();

    $(window).on('load', function() {
      // setupReadMoreModal();
      setupSimplifiedTables();
      var $ot = $('.overflow-table');
      $ot.each(function(){
        $(this).setupFixedTableRows();
      });
      setupCustomScroll();

      // setupScrollableTargets();
      setupTargetsWidth();
    });

  });
}(window, document, $));
