if (!Array.prototype.last) {
  Array.prototype.last = function () {
    return this[this.length - 1];
  };
}

(function (window, document, $) {
  var selectorFormContainer = ".wise-search-form-container";
  var exceptVal = ["all", "none", "invert", "apply"];
  /*
   * SELECT2 functions
   * */
  // TODO: please explain what this does and why it's needed
  function setupSelects2(selector) {
    var forbiddenIDs = [];
    var selectorFormCont = selector || selectorFormContainer;

    $(selectorFormCont + " select").each(function (ind, selectElement) {
      var selectedElementID = $(selectElement).attr("id");
      if (forbiddenIDs.indexOf(selectedElementID) !== -1) {
        return false;
      }

      $(selectElement).addClass("js-example-basic-single");
      var lessOptions = $(selectElement).find("option").length < 10;

      var options = {
        placeholder: "Select an option",
        closeOnSelect: true,
        dropdownAutoWidth: true,
        width: "100%",
        theme: "flat",
      };
      if (lessOptions) options.minimumResultsForSearch = Infinity;

      $(selectElement).select2(options);
    });
  }

  function initStyling() {
    // TODO: is this still needed? I don't think so
    //$("#form-buttons-continue").hide("fast");
    $(".button-field").addClass("btn");

    // mobile hide .toggle-sidebar
    $(".toggle-sidebar").hide();
  }

  function setupTargetsWidth() {
    // Make targets extend on multiple rows when there are many targets
    // and the assessment-data-table is scrollable
    var $tableWrap = $(".table-wrap");
    var $assessmentTable = $(
      "#container-assessment-data-2018 .assessment-data-table"
    );
    if ($assessmentTable.width() <= $tableWrap.width()) {
      return;
    }

    $("div.gescomp", $tableWrap).css({
      display: "inline-table",
      "min-width": "inherit",
      width: "inherit",
    });

    var maxGescompWidth = 0;
    $("div.gescomp", $tableWrap).each(function () {
      var width = $(this).width();
      if (width > maxGescompWidth) {
        maxGescompWidth = width;
      }
    });

    $("div.gescomp", $tableWrap).css({ width: maxGescompWidth });

    // $(window).on('resize', adjustTargetsWidth);
  }

  function setupScrollableTargets() {
    // NOT USED
    // create a clone of the assessment data 2018 table and overlap the original table
    // with fixed question and score columns
    $(
      "#container-assessment-data-2018 .table.table-condensed.assessment-data-table"
    )
      .clone(true)
      .appendTo("#container-assessment-data-2018")
      .addClass("clone");

    var $orig = $(".table-wrap .table.table-condensed.assessment-data-table");
    var $clone = $(".table.table-condensed.assessment-data-table.clone");
    var origLength = $orig.find("tr").length;
    var origHeight, cloneHeight;

    for (var i = 0; i < origLength; i++) {
      var x = $clone.find("tr")[i];
      cloneHeight = $(x).find(".fixed-center").innerHeight();
      origHeight = $($orig.find("tr")[i]).innerHeight();

      if (origHeight > cloneHeight) {
        $(x).css("height", origHeight + "px");
      } else {
        $($orig.find("tr")[i]).css("height", cloneHeight + "px");
      }
    }
  }

  function setupAssessmentStatusChange() {
    // Setup the process status change forms to make it possible
    // to change the assessment status on pages like
    // ./assessment-module/national-descriptors-assessments/fi/assessments
    // ./assessment-module/regional-descriptors-assessments/bal/assessments

    $(".assessment-status-processstate").each(function () {
      var $this = $(this);
      var $processState = $this.find(".process-state");

      $this.on("click", function () {
        $this.toggleClass("active");
      });
    });

    $(
      ".assessment-status-wrapper .assessment-status.process-state select"
    ).change(function () {
      var $form = $(this).parents("form");
      var $assessmentContainers = $(".assessment-status-container2");
      var url = $form[0].action;

      $(document.body).addClass("cursor-wait");
      $form.addClass("cursor-wait");
      $assessmentContainers.each(function () {
        $(this).addClass("cursor-wait");
      });

      $.ajax({
        url: url,
        type: "POST",
        data: $form.serialize(),
        success: function () {
          location.reload();
        },
      });
    });
  }

  function setupProcessStateCheckboxes() {
    $(".assessment-status-td.enable-process-state-change").each(function () {
      var $this = $(this);
      var action = $this.find(".assessment-status-wrapper form").attr("action");

      var $inputCheckbox = $("<input type='checkbox' />")
        .attr("name", "process-state-change")
        .attr("value", action)
        .appendTo($this);

      $inputCheckbox.change(function () {
        var value = $(this).attr("value");
        var ischecked = $(this).is(":checked");

        if (ischecked) {
          // when the checkbox is checked
          var inputNotExists =
            $("#form-process-state-change-bulk").find(
              "input[value='" + value + "' ]"
            ).length === 0;

          if (inputNotExists) {
            $(this)
              .clone()
              .attr("type", "hidden")
              .appendTo("#form-process-state-change-bulk");
          }

          // phase-selector pat-select2
          var $newPhaseSelector = $(this)
            .parent("td")
            .find(".phase-selector")
            .clone()
            .attr("id", "process-state-bulk-select");

          $newPhaseSelector.change(function () {
            var $form = $(this).parents("form");
            var url = $form[0].action;

            $(document.body).addClass("cursor-wait");
            $form.addClass("cursor-wait");

            $.ajax({
              url: url,
              type: "POST",
              data: $form.serialize(),
              success: function () {
                location.reload();
              },
            });
          });

          $("#form-process-state-change-bulk .phase-selector").replaceWith(
            $newPhaseSelector
          );
        } else {
          // when the checkbox is unchecked
          $("#form-process-state-change-bulk")
            .find("input[value='" + value + "' ]")
            .remove();

          // if there are no checkboxes checked, remove the select box too
          if (
            $("#form-process-state-change-bulk").find(
              "input[name='process-state-change']"
            ).length === 0
          ) {
            $("#form-process-state-change-bulk .phase-selector select").remove();
          }
        }
      });
    });
  }

  $.fn.fixTableHeaderAndCellsHeight = function () {
    // because the <th> are position: absolute, they don't get the height of
    // the <td> cells, and the other way around.

    this.each(function () {
      $("th", this).each(function (index) {
        if ($(this).parents("table").hasClass("skip-height-fix")) {
          return;
        }

        var isSideBySideLeft = $(this)
          .parents(".overflow-table")
          .hasClass("side-by-side-table-left");
        var isSideBySideRigth = $(this)
          .parents(".overflow-table")
          .hasClass("side-by-side-table-right");

        if (isSideBySideRigth) {
          return;
        }

        var $th = $(this);
        // var $next = $('td:not(".sub-header")', $th.parent());
        var $next = $th.parent().children('td:not(".sub-header")');

        if (isSideBySideLeft) {
          var $nextSideBySide = $(
            $(this)
              .parents(".overflow-table.side-by-side-table")
              .siblings(".overflow-table.side-by-side-table-right")
              .find("tr")[index]
          ).children();
          $next = $.merge($next, $nextSideBySide);
        }

        var $subheader = $("td.sub-header", $th.parent());
        var tdHeights = [];

        $next.each(function () {
          var $this = $(this);
          if ($this.hasClass("translatable")) {
            var hght = $this.find(".tr-text").height();
            tdHeights.push(hght);
          } else {
            tdHeights.push($this.height());
          }
        });

        var cells_max_height = Math.max.apply(Math, tdHeights);
        var height = Math.max(
          $th.height(),
          $subheader.height(),
          cells_max_height
        );

        $th.height(height);
        $subheader.height(height);
        var thHeight = $th.height();
        var thInnerHeight = $th.innerHeight();

        if (thHeight >= cells_max_height) {
          $next.each(function () {
            if ($(this).hasClass("translatable")) {
              $(this).height(thInnerHeight);
            } else {
              $(this).height(thHeight);
            }
          });
          //$next.height(thHeight);
        }

        $("div", this).css("margin-top", "-4px");
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
    // TODO not used anymore, replaced by fixTableHeaderAndCellsHeight

    // Because of the way the <th> cells are positioned absolute, to be able to
    // keep them fixed, they are "disconnected" from the regular box sizing
    // layout algorithm. For this reason we have to recompute their height (to
    // make either the <td> or the <th> match same height
    this.each(function () {
      if ($(this).parents("table").hasClass("skip-height-fix")) {
        return;
      }

      $("th", this).each(function (index) {
        var $th = $(this);
        var $next = $("td", $th.parent());
        var tdHeights = [];
        var isSideBySideLeft = $(this)
          .parents(".overflow-table")
          .hasClass("side-by-side-table-left");
        var isSideBySideRigth = $(this)
          .parents(".overflow-table")
          .hasClass("side-by-side-table-right");

        if (isSideBySideRigth || isSideBySideLeft) {
          return;
        }

        if (isSideBySideLeft) {
          var $rowSideBySide = $(
            $(this)
              .parents(".overflow-table.side-by-side-table")
              .siblings(".overflow-table.side-by-side-table-right")
              .find("tr")[index]
          );
          var $nextSideBySide = $rowSideBySide.children("td");
          var $thSideBySide = $rowSideBySide.children("th");
          $next = $.merge($next, $nextSideBySide);
        }

        $next.each(function () {
          var $this = $(this);
          if ($this.hasClass("translatable")) {
            var hght = $this.find(".tr-text").height();
            tdHeights.push(hght);
          } else {
            tdHeights.push($this.height());
          }
        });

        var cells_max_height = Math.max.apply(Math, tdHeights);

        $th.height(cells_max_height);
        if (isSideBySideLeft) {
          $thSideBySide.height(cells_max_height);
        }
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
    var rowLevel = $(row).data("level");
    rowLevel = rowLevel != undefined ? parseInt(rowLevel) : -1;
    $(cache.setlimits).each(function () {
      if (this.level == rowLevel) {
        limits = this.limits;
        return false;
      }
    });
    if (limits.length == 0) {
      limits = cache.setlimits[cache.setlimits.length - 1].limits;
    }

    // group cells by similarity
    $("td", row)
      .not(".sub-header")
      .each(function (ix) {
        if (sets.length == 0 || limits.includes(ix)) {
          sets.push([this]);
        } else {
          var thisText = $(this).text().trim();
          var lastText = $(sets.last().last()).text().trim();

          if (thisText == lastText) {
            sets.last().push(this);
          } else {
            sets.push([this]);
          }
        }
      });

    // merge cells that are duplicated
    $(sets).each(function () {
      if (this.length > 1) {
        var colspan = this.length;
        $(this[0]).attr("colspan", colspan); // .addClass('merged');
        $(this.slice(1)).each(function () {
          $(this).remove();
        });
      }
    });

    // compute new group limits
    if (rowLevel != -1) {
      limits = [];
      cache.curentLevel = rowLevel;

      $(sets).each(function () {
        var l = this.length;
        if (limits.length) {
          l += limits[limits.length - 1];
        }
        limits.push(l);
      });
      cache.setlimits.push({
        level: cache.curentLevel,
        limits: limits.slice(0), // makes a copy
      });
    }

    // apply special class to group end cells
    var cursor = 0;
    $("td", row)
      .not(".sub-header")
      .each(function (iy) {
        var level = cache.curentLevel;
        var l;
        var prevset;

        var c = parseInt($(this).attr("colspan") || "1");
        cursor += c;

        if (limits.includes(cursor)) {
          if (level > 0) {
            // traverse all previous limits to see which major one includes
            // this limit
            for (l = 0; l < cache.setlimits.length; l++) {
              prevset = cache.setlimits[l].limits;
              if (prevset.includes(cursor)) {
                level = cache.setlimits[l].level;
                break;
              }
            }
          }
          $(this).addClass("endgroup_" + level);
        }
      });
  }

  $.fn.simplifyTable = function simplifyTable() {
    var $table = $(this);

    if (!$table.data("original")) {
      $table.data("original", $table.html());
    }

    var cache = {
      curentLevel: 0,
      setlimits: [
        {
          level: -1,
          limits: [],
        },
      ],
    };
    $("tr", this).each(function () {
      mergeCellsInRow(this, cache);
    });

    // Laci disable
    // $table.fixTableHeaderHeight();
    // $table.fixTableHeaderAndCellsHeight();
    $table.data("simplified", $table.html());
  };

  $.fn.toggleTable = function toggleTable(onoff) {
    var original = $(this).data("original");
    var simplified = $(this).data("simplified");

    if (onoff) {
      //$(this).simplifyTable();
      $(this).html(simplified);
    } else {
      $(this).hide();
      $(this).empty().html(original);
      $(this).show();
      //setupTranslateClickHandlers();
      //setupReadMoreModal();
    }
    setupReadMoreModal();
    setupTranslateClickHandlers();
    $(this).fixTableHeaderAndCellsHeight();
  };

  /* Used in report data table create a 'read more' modal if the cell content
   * is too long
   */
  window.setupReadMoreModal = function () {
    var $table = $(".table-report");
    var $modal = $("#read-more-modal");
    var $modalContent = $(".modal-content-wrapper");
    var maxchars = 397;
    var sep = "...";
    var $cells = $table.find(".tr-text");
    $cells.each(function () {
      var t = $(this).text();
      var t_html = $(this).html();

      if (t_html.length > maxchars) {
        $(this).addClass("short");
        var sh = t_html.substr(0, 0.75 * maxchars) + sep;
        $(this).html(sh);
        $(this).on("click", function () {
          $modalContent.html(t_html);
          $modal.modal("show");
        });
      }
    });

    $(".btn-close-modal").click(function () {
      $modalContent.empty();
    });

    // Laci disable
    // $table.fixTableHeaderAndCellsHeight();
  };

  function setupReportNavigation() {
    // This is a menu that is triggered from a button. When scrolling down, it
    // sticks to the top. Allows navigation between articles/years
    var $reportnav = $("#report-data-navigation");
    $("button", $reportnav).on("click", function () {
      $(".nav-body", $reportnav).toggle();
      $(this)
        .children()
        .addClass("glyphicon")
        .toggleClass("glyphicon-menu-hamburger glyphicon-remove-circle");
      return false;
    });
    $(".nav-body", $reportnav).hide();

    // sticky report data navigation
    var $rn = $(".report-nav");
    var $title = $(".report-title");

    if ($rn.length > 0) {
      var stickyOffset = $rn.offset().top;

      $(window).scroll(function () {
        var scroll = $(window).scrollTop();
        var fixElement = scroll >= stickyOffset;
        $rn.toggleClass("sticky", fixElement);
        $title.toggleClass("fixed-title", fixElement);
      });
    }
  }

  function setupTableScrolling() {
    // TODO not used
    // When dealing with a really wide table, with wide cells, we want to keep
    // the text relatively narrow, but always keep in view that cell content
    var $ot = $(".overflow-table table");

    $ot.each(function () {
      var $tw = $(this);
      var $td = $tw.find("td");

      if (!$td.length) {
        return;
      }

      // get table header cell right position
      var $th = $tw.find("th");
      var thRight = $th.position().left + $th.outerWidth();

      $td.each(function () {
        var $this = $(this);
        var scrollTimer;

        $(".report-page-view .overflow-table .inner").scroll(function () {
          clearTimeout(scrollTimer);

          if ($this.attr("colspan") > 1) {
            var tdText = $this.find(".td-content");
            var tdLeft = $this.position().left;
            var tdRight = tdLeft + $this.outerWidth(); // get table cell right position
            var tdTextWidth = $this.find(".td-content").width();
            var thAndCellWidth = tdTextWidth + thRight;

            $this.css("height", $this.outerHeight());

            scrollTimer = setTimeout(afterScroll, 1);

            if (tdLeft < thRight) {
              tdText.addClass("td-scrolled").css("left", thRight + 5);
            } else {
              $this.css("height", "");
              tdText.removeClass("td-scrolled");
            }

            if (thAndCellWidth >= tdRight) {
              $this.addClass("td-relative");
            } else {
              $this.removeClass("td-relative");
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
  $.fn.isInViewport = function () {
    var elementTop = $(this).offset().top;
    var elementBottom = elementTop + $(this).height();

    var viewportTop = $(window).scrollTop();
    var viewportBottom = viewportTop + $(window).height();

    return elementBottom > viewportTop && elementTop < viewportBottom;
  };

  function addCustomScroll() {
    var $cs = $(
      '<div class="scroll-wrapper">' +
        '<i class="glyphicon glyphicon-th"></i>' +
        '<div class="top-scroll">' +
        '<div class="top-scroll-inner"></div>' +
        "</div>" +
        "</div>"
    );

    $cs.insertAfter($(".overflow-table").find(".inner"));
  }

  function setupCustomScroll() {
    // A fixed scrollbar at the bottom of the window for tables

    var $ot = $(".overflow-table");
    var $win = $(window);

    $ot.each(function () {
      var $t = $(this);
      // var $tParent = $t.parent();
      var $tParent = $t;
      var topScroll = $(".top-scroll", $tParent);
      var topScrollInner = topScroll.find(".top-scroll-inner");
      var tableScroll = $(".inner", $tParent);
      var tableWidth = $(".table-report", $tParent).outerWidth(
        (includeMargin = true)
      );
      var tableHeaderWidth = $("th", $tParent).width();
      var tableAndHeaderWidth = tableWidth + tableHeaderWidth;
      var customScroll = $(".scroll-wrapper", $tParent);

      topScrollInner.width(tableWidth);

      topScroll.on("scroll", function () {
        tableScroll.scrollLeft($(this).scrollLeft());
      });

      tableScroll.on("scroll", function () {
        topScroll.scrollLeft($(this).scrollLeft());
      });

      if (tableAndHeaderWidth > $t.width()) {
        $win.on("resize scroll", function () {
          var scroll = $win.scrollTop();

          if ($t.isInViewport()) {
            customScroll.addClass("fixed-scroll");
          } else {
            customScroll.removeClass("fixed-scroll");
          }

          // hide custom scrollbar when it reaches the bottom of the table
          if (
            scroll >=
            $t.offset().top + $t.outerHeight() - window.innerHeight
          ) {
            customScroll.hide();
          } else {
            customScroll.show();
          }
        });
      }
    });
  }

  function addFixedTable() {
    var $ot = $(".overflow-table");

    $ot.each(function () {
      var $table = $(this).find("table");
      var $cb = $('<input type="checkbox" class="fix-row"/>');
      var $ft = $(
        '<div class="fixed-table-wrapper">' +
          '<button title="Clear filters" class="reset-pins">' +
          '<i class="glyphicon glyphicon-remove-circle"></i>' +
          "</button>" +
          '<div class="fixed-table-inner">' +
          '<table class="table table-bordered table-striped fixed-table">' +
          "</table>" +
          "</div>" +
          "</div>"
      );

      // Register click event for button to clear all pinned rows for the current table
      $ft.find("button.reset-pins").click(function () {
        $ftw = $(this).closest(".fixed-table-wrapper");
        $ftw.removeClass("sticky-table");
        $ftw.find("tr").remove();

        $innerTable = $ftw.siblings(".inner");
        $innerTable.find("tr input").prop("checked", false);
      });

      if ($table.find("td.sub-header").length) {
        // Regional descriptors
        $table.find("td.sub-header").append($cb);
      } else {
        // National descriptors
        $table.find("th div").append($cb);
      }

      $ft.insertBefore($(this).find(".inner"));
    });
  }

  $.fn.setupFixedTableRows = function () {
    // Allows report table rows to be fixed while scrolling
    // var $ot = $('.overflow-table');
    var $ot = $(this);

    // The .each is necessary, we can have more overflow-tables
    $ot.each(function () {
      var $t = $(this);
      var $fixedTable = $t.find(".fixed-table-wrapper");
      var $th = $("th", $t.parent());
      var tableW = $(".table-report", $t).width();
      var tableScroll = $(".inner", $t);
      var fixedTableInner = $(".fixed-table-inner", $t);

      function toggleSyncScrolls(onoff) {
        function f1() {
          tableScroll.scrollLeft($(this).scrollLeft());
        }
        function f2() {
          fixedTableInner.scrollLeft($(this).scrollLeft());
        }
        if (onoff) {
          fixedTableInner.on("scroll", f1);
          tableScroll.on("scroll", f2);
        } else {
          fixedTableInner.off("scroll", f1);
          tableScroll.off("scroll", f2);
        }
      }
      toggleSyncScrolls(true);

      $t.find(".fix-row").each(function (i) {
        var val = "cb" + i++;
        // var checkBox = $(this).find('.fix-row');
        var checkBox = $(this);
        checkBox.val(val);
      });

      var checkBox = $t.find(".fix-row");
      checkBox.change(function () {
        var $this = $(this);
        var value = $this.val();
        var table = $this.closest(".overflow-table").find(".fixed-table");
        var tableWrapper = $this
          .closest(".overflow-table")
          .find(".fixed-table-wrapper");
        table.width(tableW);

        if ($this.is(":checked")) {
          tableWrapper.addClass("sticky-table");

          //for other tables find the reset button and trigger the click event
          var $parentReportSection = $this.closest(".report-section");
          var $otherReportSections =
            $parentReportSection.siblings(".report-section");
          $otherReportSections.each(function () {
            $ftw = $(this).find(".fixed-table-wrapper");
            $ftw.find("button.reset-pins").click();
          });

          // clone table row, but keep the width of the original table cells
          var target = $this.closest("tr");
          var target_children = target.children("td");
          var clone = target.clone();
          clone.children("td").width(function (i, val) {
            return target_children.eq(i).outerWidth();
          });
          clone.appendTo(table).attr("data-row", value);

          // disable for test
          //$t.find('.table').fixTableHeaderAndCellsHeight();
          // setupTableScrolling();
        } else {
          $fixedTable
            .find('tr[data-row="' + value + '"]')
            .slideUp("fast", function () {
              $(this).remove();
            });

          if (table.find("tr").length === 1) {
            tableWrapper.removeClass("sticky-table");
          }
        }

        var $cb = $fixedTable.find(".fix-row");
        $cb.change(function () {
          var $this = $(this);
          var value = $this.val();

          if ($this.closest("tr").siblings().length === 0) {
            $this.closest(".fixed-table-wrapper").removeClass("sticky-table");
          }

          $this.closest("tr").remove();
          $('.fix-row[value="' + value + '"]').prop("checked", false);
        });

        toggleSyncScrolls(false);
        fixedTableInner.scrollLeft(tableScroll.scrollLeft());
        toggleSyncScrolls(true);
      });
    });

    $(window).on("resize scroll", function () {
      if ($(".report-nav.sticky").length > 0) {
        $(".fixed-table-wrapper").each(function () {
          $(this).css("top", "56px");
        });
      } else {
        $(".fixed-table-wrapper").each(function () {
          $(this).css("top", "0");
        });
      }
    });
  };

  function setupResponsiveness() {
    // fire resize event after the browser window resizing it's completed
    var resizeTimer;
    $(window).resize(function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(doneResizing, 500);
    });

    function doneResizing() {
      // $('.table-report').fixTableHeaderHeight();
      $(".table-report").each(function () {
        $(this).fixTableHeaderAndCellsHeight();
      });
    }

    if (window.matchMedia("(max-width: 768px)").matches) {
      $(".overflow-table h5").width($(".overflow-table table").width());
    }

    // tibi: temporarily disabled. I don't know what td-content does
    // var $td = $('.overflow-table table td');
    // $td.children('div').wrapInner('<div class="td-content" />');
  }

  function setupSimplifiedTables() {
    $(".simplify-form")
      .next()
      .find(".table-report")
      .each(function () {
        $(this).simplifyTable();
      });

    $(".simplify-form button").on("click", function () {
      var onoff = $(this).attr("aria-pressed") == "true";
      $p = $(this).parent().next();
      $(".table-report", $p).toggleTable(!onoff);
      // Laci disable
      $p.setupFixedTableRows();
      setupCustomScroll();
    });
  }

  function regionalDescriptorsGroupTableHeaders() {
    var $headers = $(".first-header");
    if ($headers.length === 0) {
      return;
    }
    var compareText = "";
    var currentText = "";

    compareText = $headers[0].firstElementChild.innerText;

    for (i = 1; i < $headers.length; i++) {
      currentText = $headers[i].firstElementChild.innerText;

      if (compareText === currentText) {
        $headers[i].firstElementChild.innerText = "";
        $($headers[i - 1]).css("border-bottom", "0px");
      } else {
        compareText = currentText;
      }

      //debugger;
    }
  }

  $.fn.setupStickyRows = function () {
    // make first th element(s) with 'sticky-col' class stick to the left of the
    // screen when scrolling horizontally
    $stickyTable = $(".table-sticky-first-col");
    $stickyTable.find("tr").each(function () {
      $(this)
        .find("th.sticky-col")
        .each(function () {
          $currentTh = $(this);
          $prevTh = $(this).prev(".sticky-col");

          if ($prevTh.hasClass("sticky-col")) {
            prevWidth = $prevTh.outerWidth();
            prevLeft = parseInt($prevTh.css("left"));
            $currentTh.css({ left: prevWidth + prevLeft });
          } else {
            $currentTh.css("left", -1);
          }
        });
    });

    // Pin all rows with 'sticky-row' class
    $fixedTable = $(this).find(".fixed-table");
    var tableWrapper = $(this).find(".fixed-table-wrapper");
    tableWrapper.addClass("sticky-table");

    if ($(this).find(".inner table").hasClass("table-sticky-first-col")) {
      $fixedTable.addClass("table-sticky-first-col");
    }

    $(this)
      .find("tr.sticky-row")
      .each(function () {
        $(this)
          .children()
          .each(function () {
            var width = $(this).outerWidth();
            $(this).css("min-width", width);
            $(this).css("width", width);
            $(this).css("background-color", $(this).css("background-color"));
            $(this).css("color", $(this).css("color"));
            $(this).css("text-align", $(this).css("text-align"));
          });

        clone = $(this).clone();
        clone.appendTo($fixedTable);
      });

    // on scroll check if the all rows 'sticky-row' are displayed on screen
    // if not show the 'fixed-table' with the pinned rows
    $(window).on("resize scroll", function () {
      $(".overflow-table").each(function () {
        var $ot = $(this);
        var tableWrapper = $ot.find(".fixed-table-wrapper");
        var stickyRowsInView = [];

        $ot.find(".inner tr.sticky-row").each(function () {
          var elementTop = $(this).offset().top;
          var viewportTop = parseInt($(window).scrollTop());
          // var viewportBottom = viewportTop + $(window).height();
          var $currentOT = $(this).parents(".overflow-table");
          var otTop = $currentOT.offset().top;
          var otBottom = otTop + $currentOT.outerHeight();
          var theadHeight = $(this).parents("thead").outerHeight();

          // if this is false, we display the sticky bar on the top
          isInViewport =
            // $(this).isInViewport() ||
            // elementTop > viewportBottom
            elementTop > viewportTop || otBottom < viewportTop + theadHeight;

          stickyRowsInView.push(isInViewport);
        });

        if (stickyRowsInView.includes(false)) {
          $ot.removeClass("hidden-fixed-table");
        } else {
          $ot.addClass("hidden-fixed-table");
        }
      });
    });
  };

  $(document).ready(function ($) {
    setupReadMoreModal();
    initStyling();
    setupSelects2();
    setupReportNavigation();
    // setupTableScrolling();
    setupResponsiveness();
    addCustomScroll();
    addFixedTable();
    regionalDescriptorsGroupTableHeaders();

    $(".assessment-read-more").click(function () {
      var $this = $(this);
      $this.text(function (a, b) {
        return b.startsWith("Show")
          ? "Hide reports"
          : $(this).attr("display-text");
      });
      $this.parents().siblings(".assessment-dd-list").fadeToggle();
      $this
        .parents()
        .siblings(".text-reports-table")
        .find(".assessment-dd-list")
        .fadeToggle();
    });

    var $scrollBtn = $(".scroll-to-top");
    $(window).scroll(function () {
      if ($(this).scrollTop() > 400) {
        $scrollBtn.fadeIn();
      } else {
        $scrollBtn.fadeOut();
      }
    });

    $scrollBtn.click(function () {
      $("html, body").animate({ scrollTop: 0 }, 400);
      return false;
    });

    $(window).on("load", function () {
      // setupReadMoreModal();
      setupSimplifiedTables();
      var $ot = $(".overflow-table");
      $ot.each(function () {
        $(this).setupFixedTableRows();
        $(this).find(".table-report").fixTableHeaderAndCellsHeight();
        // when loading the screen pin all rows marked with 'sticky-row' class
        // and display them if they are not in viewport
        $(this).setupStickyRows();
      });
      setupCustomScroll();

      // setupScrollableTargets();
      setupTargetsWidth();
      setupAssessmentStatusChange();

      setupProcessStateCheckboxes();
    });
  });
})(window, document, $);
