/* global window, document, jQuery */
(function (window, document, $) {
  /*
   * ****************************************************
   * Page elements init
   * ****************************************************
   * */
  var exceptVal = ['all', 'none', 'invert', 'apply'];
  var selectorFormContainer = '.wise-search-form-container';
  var selectorLeftForm = '#wise-search-form';

  var sessionStore = storageFactory(sessionStorage);
  /*
   * Vars and $ plugins
   *
   * */
  $.randomString = function () {
    var chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz';
    var string_length = 8;
    var randomstring = '';
    for (var i = 0; i < string_length; i++) {
      var rnum = Math.floor(Math.random() * chars.length);
      randomstring += chars.substring(rnum, rnum + 1);
    }
    return randomstring;
  };

  $.getMultipartData = function (frmName, newBoundary) {
    //Start multipart formatting
    var initBoundary = newBoundary || $.randomString();
    var strBoundary = '--' + initBoundary;
    var strMultipartBody = '';
    var strCRLF = '\r\n';

    var iname = $(frmName).attr('id');

    var formData = $(frmName).serializeArray();
    //Create multipart for each element of the form

    if (formData.length === 0) {
      return false;
    }

    var res = [];
    var vals = {};

    $.each(formData, function (indx, val) {
      strMultipartBody +=
        strBoundary +
        strCRLF +
        'Content-Disposition: form-data; name="' +
        val.name +
        '"' +
        strCRLF +
        strCRLF +
        val.value +
        strCRLF;

      res.push(val.name);
      if (!vals[val.name]) vals[val.name] = [];
      vals[val.name].push(val.value);
    });

    //End the body by delimiting it
    strMultipartBody += strBoundary + '--' + strCRLF;

    //Return boundary without -- and the multipart content
    return [initBoundary, strMultipartBody, vals];
  };

  var loading = false;

  /*
   * Styling and hiding
   *
   */
  function initStyling() {
    var ajaxSpinner = $('#ajax-spinner');
    $('body').append(ajaxSpinner.clone(true).attr('id', 'ajax-spinner2'));
    ajaxSpinner.remove();

    $('.button-field').addClass('btn');
    $(selectorFormContainer + ' #s2id_form-widgets-marine_unit_id')
      .parentsUntil('.field')
      .parent()
      .hide();

    $('#form-buttons-continue').hide('fast');

    var $downloadBtn = $('#form-buttons-download');
    var $centerSection = $('.center-section');
    if ($downloadBtn.length > 0) {
      var dBtn =
        $downloadBtn.prop('outerHTML').replace('input', 'button') +
        ' <span>Download as spreadsheet</span>';
      var btnForm = $downloadBtn.parent();
      $downloadBtn.remove();
      btnForm.append($(dBtn));

      $downloadBtn = $('#form-buttons-download')
        .val('Download as spreadsheet')
        .addClass('ui button primary inverted');

      if ($centerSection.length) {
        $downloadBtn.appendTo($centerSection);
      }
    }
  }

  /*
   * CHECKBOXES functions
   * */
  function generateControlDiv() {
    var spAll =
      '<div class="controls">' +
      '<span>Select :</span><a data-value="all"><label>' +
      '<span class="label">All</span></label></a>';
    var spClear =
      '<a data-value="none"><label><span class="label">Clear all</span></label></a>';
    var invertSel =
      '<a data-value="invert"><label><span class="label">Invert selection</span></label></a>' +
      '<div class="btn btn-default apply-filters" data-value="apply"><span>Apply filters</span></div>' +
      '<div class="ui-autocomplete">' +
      '<span class=" search-icon" ></span>' +
      '<span class="search-span">' +
      '<input class="ui-autocomplete-input" type="text" />' +
      '<span class="clear-btn"></span>' +
      '</div>' +
      '</div>';
    return spAll + spClear + invertSel;
  }

  function searchAutoComplete(evtarget, $field) {
    var cheks2 = $field.find('.option .label:not(.horizontal) ');
    var labels = cheks2.parentsUntil('.option').parent();
    var inputs = labels.find('input');
    var options = labels.parent();
    var no_results = options.find('.noresults');

    if ($(evtarget).val() === '') {
      no_results.addClass('hidden');
      labels.removeClass('hidden');
      var data = $field.find('.panel').data('checked_items');
      if (data) {
        $.each(inputs, function (idx, el) {
          // 96264 in case we have an empty searchfield checked items
          // saved in previous query
          el.checked = data.indexOf(el.id) !== -1;
        });
      }
      return true;
    }

    $field.find('.apply-filters').show();
    //$(evtarget).find(".apply-filters").show();
    labels.removeClass('hidden');

    var toSearch = $(evtarget).val().toLowerCase().replace(/\s/g, '_');

    var matcher = new RegExp($.ui.autocomplete.escapeRegex(toSearch), 'i');

    var temp = {};
    var checksLabels = $field
      .find('.option .label:not(.horizontal) ')
      .map(function (ind, item) {
        temp[$(item).text().toLowerCase()] = $(item)
          .text()
          .toLowerCase()
          .replace(/\s/g, '_');
        //return temp;
        return (
          $(item)
            .text()
            .toLowerCase()
            /*.replace(/^\s+|\s+$/g, '')*/
            /*.replace(/_/g, "")*/
            .replace(/\s/g, '_')
        );
      });

    var found = [];
    $.each(temp, function (indx, item) {
      if (!matcher.test(item)) {
        found.push(indx);
      }
    });

    var tohide = cheks2.filter(function (idx, elem) {
      return found.indexOf($(elem).text().toLowerCase()) !== -1;
    });

    var toshow = cheks2.filter(function (idx, elem) {
      return found.indexOf($(elem).text().toLowerCase()) === -1;
    });
    $.each(toshow, function (ind, item) {
      $(item)
        .parentsUntil('.option')
        .parent()
        .find("[type='checkbox']")
        .prop('checked', true);
    });

    $.each(tohide, function (inx, item) {
      $(item)
        .parentsUntil('.option')
        .parent()
        .find("[type='checkbox']")
        .prop('checked', false);
      $(item)
        .parentsUntil('.option')
        .parent()
        .find("input[type='checkbox']")
        .prop('checked', false);
      $(item)
        .parentsUntil('.option')
        .parent()
        .find("input[type='checkbox']")
        .removeAttr('checked');
      $(item).parentsUntil('.option').parent().addClass('hidden');
    });

    if (tohide.length === cheks2.length) {
      no_results.removeClass('hidden');
    } else {
      no_results.addClass('hidden');
    }
  }

  function addAutoComplete($field) {
    $field.find('.ui-autocomplete-input').autocomplete({
      minLength: 0,
      source: [],
      search: function (event) {
        searchAutoComplete(event.target, $field);
      },
      create: function () {
        var that = this;
        var removeBtn = $(this)
          .parentsUntil('.ui-autocomplete')
          .find('.clear-btn ');
        removeBtn.on('click', null, that, function (ev) {
          $(this).parentsUntil('.controls').find('input').val('');
          $(this).parentsUntil('.controls').find('input').trigger('change');
          $(ev.data).autocomplete('search', 'undefined');
        });
      },
    });
  }

  function addCheckboxPanel($field, fieldId, cheks) {
    $field.addClass('panel-group');

    var $label = $field.find('> label.horizontal');
    $label.addClass('panel-title panel-heading');

    var $content = $label.next('.wrapped-content');
    if (!$content.length) {
      $label.nextAll().wrapAll('<div class="wrapped-content"></div>');
      $content = $label.next('.wrapped-content');
    }

    var chekspan = $content.find('> span:not(.controls)');
    chekspan.addClass('panel-default');

    $content.hide().removeClass('open');
    $label.removeClass('open');

    $label.off('click.accordion').on('click.accordion', function (e) {
      e.stopPropagation();

      var $thisLabel = $(this);
      var $thisContent = $thisLabel.next('.wrapped-content');

      if ($thisContent.is(':visible')) {
        $thisContent.hide().removeClass('open');
        $thisLabel.removeClass('open');
      } else {
        $('.wrapped-content').hide().removeClass('open');
        $('.panel-title').removeClass('open');

        $thisContent.show().addClass('open');
        $thisLabel.addClass('open');
      }
    });

    $(document)
      .off('click.accordionOutside')
      .on('click.accordionOutside', function (e) {
        if ($(e.target).closest('.panel-group').length === 0) {
          $('.wrapped-content').hide().removeClass('open');
          $('.panel-title').removeClass('open');
        }
      });

    // $field.addClass('panel-group');
    // var label = $field.find('.horizontal.panel-title');
    // label.nextAll().wrapAll('<div class="wrapped-content"></div>');

    // var chekspan = $field.find('> span:not(.controls)');
    // chekspan
    //   .addClass(fieldId + '-collapse')
    //   .addClass('collapse')
    //   .addClass('panel')
    //   .addClass('panel-default');

    // // Ensure panel and controls are collapsed/hidden by default
    // chekspan.removeClass('in show').hide();
    // $field.find('.controls').hide();

    // var label = $field.find('.horizontal');

    // var alabel =
    //   "<a data-toggle='collapse' class='accordion-toggle' >" +
    //   label.text() +
    //   '</a>';
    // label.html(alabel);

    // label.addClass('panel-heading panel-title');

    // label.attr('data-toggle', 'collapse');
    // label.attr('data-target', '.' + fieldId + '-collapse');

    // $field.find('.accordion-toggle').addClass('accordion-after');

    // // hidden-colapse event
    // chekspan.on('hidden.bs.collapse', function () {
    //   chekspan.fadeOut('fast');
    //   $field.find('.controls').slideUp('fast');
    //   $field.css({ 'border-bottom': '1px solid #ccc;' });
    // });

    // // show accordion
    // chekspan.on('show.bs.collapse', function () {
    //   chekspan.fadeIn('fast');
    //   $field.find('.controls').slideDown('fast');
    //   $field.find('> span').css({ display: 'block' });
    //   $field.find('.accordion-toggle').addClass('accordion-after');
    // });

    // // hide accordion
    // chekspan.on('hide.bs.collapse', function () {
    //   window.setTimeout(function () {
    //     $field.find('.accordion-toggle').removeClass('accordion-after');
    //   }, 600);
    // });

    if (cheks.length < 6) {
      $field.find('.controls .ui-autocomplete').hide();
    } else {
      chekspan.append("<span class='noresults hidden'>No results found</span>");
      chekspan.data('checked_items', []);

      var data = chekspan.data('checked_items');
      $.each($field.find('input:checked'), function (idx, el) {
        data.push(el.id);
      });

      addAutoComplete($field);
    }
  }

  function sortCheckboxesByChecked($field) {
    if (
      window.WISE !== undefined &&
      window.WISE.blocks !== undefined &&
      window.WISE.blocks.indexOf($field.attr('id')) !== -1
    ) {
      return;
    }
    var arr = [];
    $.each(
      $field.find(".option input[type='checkbox']:not(:checked)"),
      function (ix, ch) {
        arr.push($(ch).parent());
      },
    );
    var found = $field.find(".option input[type='checkbox']:checked");
    var foundArr = [];
    if (found.length > 0) {
      $.each(found, function (ix, item) {
        foundArr.push($(item).parent());
      });
    }
    var all = foundArr.concat(arr);

    $.each(all, function (ix, ch) {
      $field.find('.panel').append(ch);
    });
  }

  // enable autosubmit handler
  function fieldAutoSubmitSetup(fieldId, $field) {
    $('#' + fieldId).on('click', '.option', function () {
      var self = this;
      $('#ajax-spinner2').hide();
      //window.WISE.blocks = window.WISE.blocks.sort().filter((x, i, a) => !i || x != a[i-1]);

      if (
        window.WISE.blocks.indexOf(
          $(this).parentsUntil('.field').parent().attr('id'),
        ) !== -1
      ) {
        sortCheckboxesByChecked($field);
      } else {
        //TODO : check if apply-filters shown
        // each checkbox does auto submit
        window.setTimeout(function () {
          $(
            selectorFormContainer + ' .formControls #form-buttons-continue',
          ).trigger('click', { button: self });
        }, 300);
      }
    });
  }

  function generateCheckboxes($fields, $fieldsnr) {
    var count = $fieldsnr;
    $fields.each(function (indx, field) {
      var $field = $(field);
      var cheks = $field.find('.option');
      var allcheckboxes = cheks.find("input[type='checkbox']");
      var hasChecks = allcheckboxes.length > 0;
      // has checkboxes
      if (hasChecks) {
        var fieldId = $field.attr('id');

        fieldAutoSubmitSetup(fieldId, $field);

        // add "controls"
        var all = generateControlDiv();
        $field.find('> label.horizontal').after(all);

        //tooltips
        cheks.each(function (idx) {
          var text = $(cheks[idx]).text();
          $(cheks[idx]).attr('title', text.trim());
        });

        if (cheks.length < 4) {
          $field.find('.controls a').hide();
          $field
            .find('.controls')
            .html('')
            .css('height', '1px')
            .css('padding', 0);
        } else {
          addCheckboxPanel($field, fieldId, cheks);

          $field.find('.search-icon').on('click', function (ev) {
            $(ev.target).parent().find('input').trigger('focus');
          });
        }

        sortCheckboxesByChecked($field);
      }
      if (!--count)
        $(selectorFormContainer + ',' + selectorLeftForm).animate(
          { opacity: 1 },
          1000,
        );
    });
  }

  function checkboxHandlerAll(ev) {
    ev.preventDefault();

    var par = $(this).parent().parent();

    window.WISE.blocks.push($(this).parentsUntil('.field').parent().attr('id'));

    par.find('.apply-filters').show();
    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    $.each(rest, function (idx) {
      if ($(rest[idx]).val() !== 'all' && $(rest[idx]).val() !== 'none')
        $(rest[idx]).prop('checked', true);
    });
  }

  function checkboxHandlerNone(ev) {
    ev.preventDefault();

    $(this).prop('checked', false);
    var par = $(this).parent().parent();
    par.find('.apply-filters').show();
    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    window.WISE.blocks.push($(this).parentsUntil('.field').parent().attr('id'));

    $.each(rest, function (idx) {
      $(rest[idx]).prop('checked', false);
    });
  }

  function checkboxHandlerInvert(ev) {
    ev.preventDefault();
    $(this).prop('checked', false);

    var par = $(this).parent().parent();
    par.find('.apply-filters').show();

    window.WISE.blocks.push($(this).parentsUntil('.field').parent().attr('id'));

    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    var checked = rest.filter(function (ind, item) {
      return $(item).is(':checked');
    });

    var unchecked = rest.filter(function (ind, item) {
      return !$(item).is(':checked');
    });

    $.each(checked, function (idx) {
      $(checked[idx]).prop('checked', false);
    });

    $.each(unchecked, function (idx) {
      $(unchecked[idx]).prop('checked', true);
    });
  }

  function addCheckboxHandlers() {
    var $controls = $('.controls');
    $controls.on('click', "a[data-value='all']", checkboxHandlerAll);
    $controls.on('click', "a[data-value='none']", checkboxHandlerNone);
    $controls.on('click', "a[data-value='invert']", checkboxHandlerInvert);
    //$(".controls .apply-filters").on("click", $( selectorFormContainer + " .formControls #form-buttons-continue").trigger("click") );

    $controls.one('click', '.apply-filters', function () {
      $(selectorFormContainer + " [name='form.widgets.page']").val(0);
      $(
        selectorFormContainer + ' .formControls #form-buttons-continue',
      ).trigger('click', { button: this });
    });
  }

  function filterInvalidCheckboxes(cbxs) {
    return cbxs.filter(function (idx, item) {
      return exceptVal.indexOf($(item).val()) === -1;
    });
  }

  function addCheckboxLabelHandlers() {
    var allch = $(selectorFormContainer + ', ' + selectorLeftForm).find(
      '[data-fieldname]',
    );

    var triggerClick = function (chV, ev) {
      //reset page
      $(selectorFormContainer + " [name='form.widgets.page']").val(0);
      if (exceptVal.indexOf(chV) === -1)
        $(ev.target).find("input[type='checkbox']").trigger('click');
    };

    // listener for click on the whole span
    allch.on('click', '.option', function (ev) {
      $('#ajax-spinner2').hide();
      var checkboxV = $(this).find("input[type='checkbox']").val();
      if (
        window.WISE.blocks.indexOf(
          $(this).parentsUntil('.field').parent().attr('id'),
        ) !== -1
      ) {
        //return false;
      } else {
        triggerClick(checkboxV, ev);
      }
    });
  }
  /*
   * CHECKBOXES functions END
   * */

  /*
   * SELECT2 functions
   * */
  function setupRightSelects2(selector) {
    var forbiddenIDs = [
      'form-widgets-member_states-from',
      'form-widgets-member_states-to',
    ];
    var selectorFormCont = selector || selectorFormContainer;

    $(selectorFormCont + ' select').each(function (ind, selectElement) {
      var selectedElementID = $(selectElement).attr('id');
      if (forbiddenIDs.indexOf(selectedElementID) !== -1) {
        return false;
      }

      $(selectElement).addClass('js-example-basic-single');
      var lessOptions = $(selectElement).find('option').length < 10;

      var $wise_search_form = $(selectorFormCont);

      var options = {
        placeholder: 'Select an option',
        closeOnSelect: true,
        dropdownAutoWidth: true,
        width: '100%',
        theme: 'flat',
      };
      if (lessOptions) options.minimumResultsForSearch = Infinity;

      $(selectElement).select2(options);

      $(selectorFormCont + ' #s2id_form-widgets-marine_unit_id').hide();

      var removePaginationButtons = function () {
        // $wise_search_form.find("[name='form.buttons.prev']").remove();
        // $wise_search_form.find("[name='form.buttons.next']").remove();
        $wise_search_form.find("[name='form.widgets.page']").remove();
      };

      $(selectElement).on('select2-selecting', function (ev) {
        // remove results following form-widgets-article select element
        // as we want to reset each facet to it's initial value if we change form
        if ($(this).attr('id') === 'form-widgets-article') {
          //$(ev.target).closest(".form-right-side").next().remove();
        }

        removePaginationButtons();

        var self = this;
        window.setTimeout(function () {
          $(selectorFormCont + ' .formControls #form-buttons-continue').trigger(
            'click',
            { select: self },
          );
        }, 300);
      });
    });
  }

  function formatArticle(article) {
    var el = $(article.element[0]);
    var subtitle = el.attr('data-subtitle');

    return '<span>' + el.attr('data-maintitle') + ': ' + subtitle + '</span>';
  }

  function marineUnitSelect() {
    var $selectArticle = $('#mobile-select-article');

    var moptions = {
      placeholder: 'Select an option',
      closeOnSelect: true,
      // dropdownAutoWidth: true,
      // width: 'auto',
      width: 'element',
      theme: 'flat',
      minimumResultsForSearch: 20,
      formatSelection: formatArticle,
      formatResult: formatArticle,
      containerCssClass: 'mobile-select-article',
    };

    if ($.fn.select2 !== undefined) {
      $selectArticle.select2(moptions);
      $selectArticle.one('select2-selecting', function (ev) {
        document.location.href = ev.choice.id;
      });
    }
  }

  function setupLeftSelect2() {
    var marineUnitTriggerSelector = '#marine-unit-trigger';
    if (
      $(selectorLeftForm + ' select:not(.notselect)').hasClass(
        'js-example-basic-single',
      )
    ) {
      return false;
    }
    $(selectorLeftForm + ' select:not(.notselect)')
      .addClass('js-example-basic-single')
      .each(function (ind, selectElement) {
        var options = {
          placeholder: 'Select an option',
          closeOnSelect: true,
          dropdownAutoWidth: false,
          width: 'auto',
          theme: 'flat',
          minimumResultsForSearch: 20,
          allowClear: true,
          dropdownParent: '#marine-unit-trigger',
          dropdownAdapter: 'AttachContainer',
          containerCssClass: 'select2-top-override',
          dropdownCssClass: 'select2-top-override-dropdown',
          debug: true,
        };

        $(selectElement).select2(options);

        // david
        $(selectElement)
          .parentsUntil('.field')
          .parent()
          .prepend('<h4>Marine Unit ID: </h4>');

        $(selectElement).on('select2-open', function () {
          var trh = $(marineUnitTriggerSelector).offset().top;
          //$(".select2-top-override-dropdown").css("margin-top", $("#marine-unit-trigger").height()/2 + "px" );
          $(marineUnitTriggerSelector + ' .arrow').hide();
          $('.select2-top-override-dropdown').css({
            top:
              trh +
              $(marineUnitTriggerSelector).height() -
              $(marineUnitTriggerSelector + ' .arrow').height() +
              'px',
            'margin-top': '12' + 'px !important',
          });
        });

        $(selectElement).on('select2-selecting', function (ev) {
          //$(selectorLeftForm + " "+  marineUnitTriggerSelector +"  a").text(ev.object.text);

          $(selectorFormContainer + " [name='form.widgets.page']").val(0);
          $(selectorFormContainer + ' #form-widgets-marine_unit_id')
            .select2()
            .val(ev.val)
            .trigger('change');
          $(
            selectorFormContainer + ' .formControls #form-buttons-continue',
          ).trigger('click', { select: ev.target, from_marine_widget: true });
        });

        $(selectElement).on('select2-close', function () {
          $(marineUnitTriggerSelector).css('background', 'transparent');
          $(marineUnitTriggerSelector + ' a').css('background', 'transparent');
          $(marineUnitTriggerSelector + ' .arrow').show();
        });

        /// Marine Unit id selector
        if (
          $(selectorLeftForm + ' select').hasClass('js-example-basic-single')
        ) {
          // Select2 has been initialized
          var text = $(
            selectorLeftForm +
              ' select [value="' +
              jQuery(selectorLeftForm + ' .select-article select').val() +
              '"]',
          ).text();
          $(selectorLeftForm + ' select:not(.notselect)')
            .parentsUntil('.field')
            .before(
              '<div id="marine-unit-trigger">' +
                '<div class="text-trigger">' +
                text +
                '</div>' +
                '</div>',
            );

          $(marineUnitTriggerSelector).on('click', function () {
            if (loading) return false;
            $(marineUnitTriggerSelector).css(
              'background',
              'rgb(238, 238, 238)',
            );
            $(marineUnitTriggerSelector + ' a').css(
              'background',
              'rgb(238, 238, 238)',
            );

            $(selectorLeftForm + ' select:not(.notselect)').select2('open');

            var trH = $(marineUnitTriggerSelector + ' a').height();
            $('.select2-top-override-dropdown').css(
              'margin-top',
              trH / 2 + 'px',
            );
          });
        }
      });
  }

  function attachSelect2() {
    setupRightSelects2();
    setupLeftSelect2();
    marineUnitSelect();

    var w = 'auto';
    var daw = true;
    if (window.matchMedia('(max-width: 967px)').matches) {
      w = false;
      daw = false;
    }

    var options = {
      placeholder: 'Select an option',
      closeOnSelect: true,
      dropdownAutoWidth: daw,
      width: w,
      theme: 'flat',
      minimumResultsForSearch: 20,
      containerCssClass: 'extra-details-select',
    };

    $.each(
      $(selectorLeftForm + ' .extra-details-select'),
      function (idx, elem) {
        if ($(elem).find('option').length > 1) {
          $(elem).select2(options);
        } else {
          $(elem).hide();
          //$(elem).after("<span>"+ $($(elem).find("option")[0]).attr("title") +"</span>");
        }
      },
    );

    $(selectorLeftForm + ' .extra-details .tab-panel').fadeOut(
      'slow',
      function () {
        $.each(
          $(selectorLeftForm + ' .extra-details .extra-details-section'),
          function (indx, item) {
            $($(item).find('.tab-panel')[0]).show();
          },
        );
      },
    );

    $(selectorLeftForm + ' .extra-details-select').on(
      'select2-selecting',
      function (ev) {
        var sect = $(ev.target).parentsUntil('.extra-details-section').parent();
        $.each($(sect).find('.tab-panel'), function (idx, elem) {
          if ($(elem).attr('id') !== ev.choice.id) {
            $(elem).hide();
          } else {
            $(elem).fadeIn();
          }
        });
      },
    );

    if ($(selectorLeftForm + ' .tab-content .tab-pane.fade').length > 0) {
      $(
        $(
          selectorLeftForm +
            ' .tab-content.msfd-extra-tab-content .tab-pane.fade',
        )[0],
      ).addClass('in active');
      $(
        $(selectorLeftForm + ' .nav-tabs.msfd-extra-nav-tabs .nav-item')[0],
      ).addClass('active');
    }
  }
  /*
   * SELECT2 functions END
   * */

  function marineBtnHandler(ev) {
    var direction = ev.data.direction;
    var marinUidSelect = $(
      selectorFormContainer + ' #s2id_form-widgets-marine_unit_id',
    );
    var selectedV = marinUidSelect.select2('data');

    var nextEl = $(selectedV.element[0]).next();
    var prevEl = $(selectedV.element[0]).prev();

    if (direction === 'next') {
      var dir = nextEl.val();
    } else if (direction === 'prev') {
      var dir = prevEl.val();
    }

    // reset paging
    $(selectorFormContainer + " [name='form.widgets.page']").remove();

    $(selectorFormContainer + ' #form-widgets-marine_unit_id')
      .select2()
      .val(dir)
      .trigger('change', { from_marine_widget: true });
    $(selectorFormContainer + ' #s2id_form-widgets-marine_unit_id').hide();

    //$(selectorFormContainer + " .formControls #form-buttons-continue").trigger("click");
    $(selectorFormContainer + ' .formControls #form-buttons-continue').trigger(
      'click',
    );
  }

  function setPaginationButtons() {
    var prevButton = $(".msfd-search-wrapper [name='form.buttons.prev']");
    var nextButton = $(".msfd-search-wrapper [name='form.buttons.next']");
    var continueBtn = '.formControls #form-buttons-continue';

    prevButton.one('click', function () {
      if (loading) return false;
      $(selectorFormContainer)
        .find('form')
        .append("<input type='hidden' name='form.buttons.prev' value='Prev'>");
      $(selectorFormContainer).find(continueBtn).trigger('click');
    });

    nextButton.one('click', function () {
      if (loading) return false;
      $(selectorFormContainer)
        .find('form')
        .append("<input type='hidden' name='form.buttons.next' value='Next'>");
      $(selectorFormContainer).find(continueBtn).trigger('click');
    });

    var selected = $(selectorLeftForm + ' select:not(.notselect)').val();

    var opts = $(selectorLeftForm + ' select:not(.notselect) option');
    var formBtnPrevTop = '#form-buttons-prev-top';
    var formBtnNextTop = '#form-buttons-next-top';
    var marineUnitTrigger = '#marine-unit-trigger';

    $('#marine-unit-nav').hide();
    // ignore 1st option for "prev" button
    if (
      $(selectorLeftForm + ' select:not(.notselect)').val() !== $(opts[1]).val()
    ) {
      var topPrevBtn =
        '<button type="submit" id="form-buttons-prev-top" name="marine.buttons.prev"' +
        ' class="submit-widget button-field btn btn-default pagination-prev" value="" button="">' +
        '          </button>';

      $(formBtnPrevTop).append(topPrevBtn);

      $(formBtnPrevTop).on(
        'click',
        null,
        { direction: 'prev' },
        marineBtnHandler,
      );
      $(formBtnPrevTop).hide();
      $(marineUnitTrigger + ' .arrow-left-container').one('click', function () {
        $(formBtnPrevTop).trigger('click');
      });
    } else {
      $(marineUnitTrigger + ' .arrow-left-container').hide();
      $('.text-trigger').css('margin-left', 0);
    }

    // ignore last option for "next" button
    if (
      $(selectorLeftForm + ' select:not(.notselect)').val() !==
      $(opts[opts.length - 1]).val()
    ) {
      var topNextBtn =
        '<button type="submit" ' +
        'id="form-buttons-next-top" name="marine.buttons.next" class="submit-widget button-field btn btn-default pagination-next" value="">' +
        '            </button>';

      $(formBtnNextTop).append(topNextBtn);

      $(formBtnNextTop).on(
        'click',
        null,
        { direction: 'next' },
        marineBtnHandler,
      );
      $(formBtnNextTop).hide();
      $(marineUnitTrigger + ' .arrow-right-container').one(
        'click',
        function () {
          $('#form-buttons-next-top').trigger('click');
        },
      );
    } else {
      $(marineUnitTrigger + ' .arrow-right-container').hide();
    }
  }

  var paginationTextResult = '.pagination-text > span:first-child';

  function initPaginationInput() {
    // check if results more than 2, if not then disable
    if (parseInt($($('.pagination-text > span:nth-child(2)')[0]).text()) < 3) {
      return false;
    }

    $(paginationTextResult).addClass('pagination-result');

    if ($(paginationTextResult).parent().find('input').length === 0) {
      $(paginationTextResult).after(
        '<input type="text" class="pagination-input" />',
      );
      $('.pagination-text .pagination-input').hide();

      paginationInputHandlers();
    }

    $('.msfd-search-wrapper').on('click', paginationTextResult, function (ev) {
      $(ev.target)
        .parent()
        .find('input')
        .show(300)
        .focus()
        .css('display', 'inline-block');
      $(ev.target).hide();
    });

    $('.msfd-search-wrapper').on('click', function (ev) {
      // if click is on the result text
      if (
        $(ev.target).is(paginationTextResult) ||
        $(ev.target).is('.pagination-text .pagination-input')
      ) {
      } else {
        $(paginationTextResult).parent().find('input').hide();
        $(paginationTextResult).show();
      }
    });
  }

  function paginationInputHandlers() {
    var inp = $('.pagination-text .pagination-input');

    // hide pagination input on focus out
    /*inp.on("focusout", function (){
            inp.hide();
            $(paginationTextResult).show();
        });*/

    // pagination input delay auto-submit
    inp.bind('focusout', function (e) {
      var val = $(e.target).val();
      var maximum = parseInt($($(e.target).parent().find('> span')[1]).text());

      if (loading) {
        return false;
      }

      var _this = $(this);
      var validateNr = function (x, maximum) {
        if (isNaN(parseInt(x))) {
          return false;
        } else {
          x = parseInt(x);
          var res = $($(paginationTextResult)[0]).text();
          if (x === parseInt(res)) {
            return false;
          }
          if (x > maximum) {
            return maximum - 1;
          }
          if (x <= 0) {
            return false;
          }
        }
        return x === 1 ? 0 : x - 1;
      };
      var validator = validateNr(val, maximum);
      if (validator !== false) {
        $(selectorFormContainer + " [name='form.widgets.page']").val(validator);
        $(paginationTextResult).text(val);
        $(paginationTextResult).show();
        $(paginationTextResult).parent().find('input').hide();
        $(
          selectorFormContainer + ' .formControls #form-buttons-continue',
        ).trigger('click');
      } else {
        $(e.target).val('');
        $(paginationTextResult).parent().find('input').hide();
        $(paginationTextResult).show();
      }
    });
  }

  function initPageElems() {
    // move marine unit id below form title and pagination as seen on the
    // other article tabs
    var pagination = $('.prev-next-row').eq(0);
    if (pagination.length) {
      $('#marine-widget-top').detach().insertBefore(pagination);
    }

    initStyling();

    var $fields = $(selectorFormContainer + ', ' + selectorLeftForm).find(
      '[data-fieldname]',
    );
    if ($fields.length > 0) {
      generateCheckboxes($fields, $fields.length);
    }

    $(selectorFormContainer + ',' + selectorLeftForm).animate(
      { opacity: 1 },
      1000,
    );

    var $heading = $('.msfd-heading');
    var $startLink = $('.msfd-start-link');
    if ($heading.length && $startLink.length) {
      $heading.insertAfter($startLink);
    }

    addCheckboxHandlers($(selectorFormContainer));
    addCheckboxLabelHandlers();
    attachSelect2();

    if ('undefined' !== typeof window.setupTabs && null !== window.setupTabs)
      window.setupTabs();

    if ('undefined' !== typeof clickFirstTab && null !== clickFirstTab)
      clickFirstTab();

    setPaginationButtons();
    initPaginationInput();
  }

  /*
   * Form handlers
   * */
  function beforeSendForm(jqXHR, settings) {
    window.WISE.blocks = [];
    //$("#ajax-spinner2").hide();

    $(selectorLeftForm + ' .no-results').remove();

    var t = "<div id='wise-search-form-container-preloader'/>";
    var sp = $('#ajax-spinner2').attr('id', 'ajax-spinner-form').show();

    $(selectorFormContainer).append(t);
    $('#wise-search-form-container-preloader').append(sp);

    $('#form-widgets-marine_unit_id').prop('disabled', true);
    //$("s2id_form-widgets-marine_unit_id").select2("enable",false);
    $("[name='form.buttons.prev']").prop('disabled', true);
    $("[name='form.buttons.next']").prop('disabled', true);

    $("[name='marine.buttons.prev']").prop('disabled', true);
    $("[name='marine.buttons.next']").prop('disabled', true);

    if ($('#marine-widget-top').length > 0) {
      var cont = $('#marine-widget-top').next();
      cont.css('position', 'relative');
    } else {
      cont = $('.left-side-form');
    }

    cont.prepend("<div id='wise-search-form-preloader'/>");

    $('#wise-search-form-preloader').append(
      "<span style='position: absolute;" +
        ' display: block;' +
        ' left: 50%;' +
        "top: 10%;'></span>",
    );
    $('#wise-search-form-preloader > span').append(
      $('#ajax-spinner2').clone().attr('id', 'ajax-spinner-center').show(),
    );

    $('#ajax-spinner-center').css({
      position: 'fixed',
      //"top" : "50%",
      //"left" : "30%",
      // "transform" : "translateX(-50%)"
    });

    $('#wise-search-form-top').find('.alert').remove();
    //window.WISE.marineUnit = $(selectorLeftForm + " select").val(  );

    loading = true;
  }

  function formSuccess(data, status, req) {
    $(selectorLeftForm + ' #wise-search-form-top')
      .siblings()
      .html('');
    $(selectorLeftForm + ' #wise-search-form-top')
      .siblings()
      .fadeOut('fast');

    $(selectorLeftForm + ' .topnav')
      .next()
      .remove();

    var $data = $(data);

    window.WISE.formData = $(data).find(selectorFormContainer).clone(true);

    var chtml = $data.find(selectorFormContainer);

    var fhtml = chtml.html();

    console.log('success');
    $('#wise-search-form-preloader').remove();

    var centerContentD = $data
      .find(selectorLeftForm + ' #wise-search-form-top')
      .siblings();

    $(selectorFormContainer).html(fhtml);

    if ($data.find(selectorLeftForm + ' .topnav').next().length > 0) {
      $(selectorLeftForm + ' .topnav').after(
        $data.find(selectorLeftForm + ' .topnav').next(),
      );
    }

    $(selectorLeftForm + ' #wise-search-form-top')
      .siblings()
      .remove();
    $(selectorLeftForm + ' #wise-search-form-top').after(centerContentD);

    /*var res = $data.find( selectorLeftForm );

        if(res.children().length === 1){
            if($(res[0]).attr("id") === "wise-search-form-top" ){
                $( selectorLeftForm + " #wise-search-form-top").after("<span class='no-results'>No results found.</span>");
            }

        }*/

    initPageElems();
    var formAction = $('.wise-search-form-container form').attr('action') || '';
    if (formAction.includes('/marine/++api++')) {
      var newFormAction = formAction;
    } else {
      var newFormAction = formAction.replace('/marine', '/marine/++api++');
    }

    $('.wise-search-form-container form').attr('action', newFormAction);
    removeNoValues();
    fixTableHeaderAndCellsHeight();
    //addDoubleScroll();

    $("[name='form.buttons.prev']").prop('disabled', false);
    $("[name='form.buttons.next']").prop('disabled', false);

    $("[name='marine.buttons.prev']").prop('disabled', false);
    $("[name='marine.buttons.next']").prop('disabled', false);
    $('#wise-search-form-top').find('.alert').remove();
  }

  /* - table_sorter.js - */
  /********* Table sorter script *************/
  /*
   * For all table elements with 'listing' class,
   * when user clicks on a th without 'nosort' class,
   * it sort table values using the td class with 'sortabledata-mydata' name,
   * or the td text content
   *
   */
  function sortabledataclass(cell) {
    var re, matches;

    re = new RegExp('sortabledata-([^ ]*)', 'g');
    matches = re.exec(cell.attr('class'));
    if (matches) {
      return matches[1];
    } else {
      return null;
    }
  }

  function sortable(cell) {
    // convert a cell a to something sortable

    // use sortabledata-xxx cell class if it is defined
    var text = sortabledataclass(cell);
    if (text === null) {
      text = cell.text();
    }

    // A number, but not a date?
    if (
      text.charAt(4) !== '-' &&
      text.charAt(7) !== '-' &&
      !isNaN(parseFloat(text))
    ) {
      return parseFloat(text);
    }
    return text.toLowerCase();
  }

  function sort() {
    var th, colnum, table, tbody, reverse, index, data, usenumbers, tsorted;

    th = $(this).closest('th');
    colnum = $('th', $(this).closest('thead')).index(th);
    table = $(this).parents('table:first');
    tbody = table.find('tbody:first');
    tsorted = parseInt(table.attr('sorted') || '-1', 10);
    reverse = tsorted === colnum;

    $(this).parent().find('th:not(.nosort) .sortdirection').html('&#x2003;');
    $(this)
      .children('.sortdirection')
      .html(reverse ? '&#x25b2;' : '&#x25bc;');

    (index = $(this).parent().children('th').index(this)),
      (data = []),
      (usenumbers = true);
    tbody.find('tr').each(function () {
      var cells, sortableitem;

      cells = $(this).children('td');
      sortableitem = sortable(cells.slice(index, index + 1));
      if (isNaN(sortableitem)) {
        usenumbers = false;
      }
      data.push([
        sortableitem,
        // crude way to sort by surname and name after first choice
        sortable(cells.slice(1, 2)),
        sortable(cells.slice(0, 1)),
        this,
      ]);
    });

    if (data.length) {
      if (usenumbers) {
        data.sort(function (a, b) {
          return a[0] - b[0];
        });
      } else {
        data.sort();
      }
      if (reverse) {
        data.reverse();
      }
      table.attr('sorted', reverse ? '' : colnum);

      // appending the tr nodes in sorted order will remove them from their old ordering
      tbody.append(
        $.map(data, function (a) {
          return a[3];
        }),
      );
      // jquery :odd and :even are 0 based
      tbody.each(setoddeven);
    }
  }

  function setoddeven() {
    var tbody = $(this);
    // jquery :odd and :even are 0 based
    tbody
      .find('tr')
      .removeClass('odd')
      .removeClass('even')
      .filter(':odd')
      .addClass('even')
      .end()
      .filter(':even')
      .addClass('odd');
  }

  function formAjaxComplete(jqXHR, textStatus) {
    if (textStatus === 'success') {
      $(selectorFormContainer).fadeIn('fast', function () {
        $(selectorLeftForm + ' #wise-search-form-top')
          .siblings()
          .fadeIn('fast');
      });
    }

    // $(selectorFormContainer).find("[name='form.buttons.prev']").remove();
    // $(selectorFormContainer).find("[name='form.buttons.next']").remove();

    //$("s2id_form-widgets-marine_unit_id").select2().enable(true);

    $(selectorLeftForm + ' #loader-placeholder').remove();

    $('#form-widgets-marine_unit_id').prop('disabled', false);

    //if($( selectorLeftForm + " select").val() === "--NOVALUE--" ) $( selectorLeftForm + " select").val(window.WISE.marineUnit).trigger("change.select2");
    if ($(selectorLeftForm + ' select').hasClass('js-example-basic-single')) {
      // Select2 has been initialized
      if (
        $(selectorLeftForm + ' .select2-choice').width() / 2 <=
        $(selectorLeftForm + ' #select2-chosen-3').width()
      ) {
        $(selectorLeftForm + ' .select2-choice').css('width', '50%');
      } else if (
        2 * ($(selectorLeftForm + ' .select2-choice').width() / 3) <=
        $(selectorLeftForm + ' #select2-chosen-3').width()
      ) {
        $(selectorLeftForm + ' .select2-choice').css('width', '70%');
      }
    }

    if ($('#wise-search-form-top').next().length === 0) {
      $(selectorLeftForm + ' #wise-search-form-top').after(
        "<span class='no-results'>No results found.</span>",
      );
    }

    loading = false;

    // set up blank spaceholder gif
    var blankarrow = $('<span>&#x2003;</span>').addClass('sortdirection');
    // all listing tables not explicitly nosort, all sortable th cells
    // give them a pointer cursor and  blank cell and click event handler
    // the first one of the cells gets a up arrow instead.
    $('table.listing:not(.nosort) thead th:not(.nosort)')
      .append(blankarrow.clone())
      .css('cursor', 'pointer')
      .click(sort);
    $('table.listing:not(.nosort) tbody').each(setoddeven);

    if (typeof scanforlinks !== 'undefined') jQuery(scanforlinks);

    addDoubleScroll();
  }

  function formAjaxError(req, status, error) {
    /*if(window.WISE.formData.length > 0){
            var data = $($(window.WISE.formData)[0]).find(".field");
            $.each( data , function (indx, $field) {
                var chk = $($field).find(".option input[type='checkbox']:checked");
                if(chk.length > 0){
                    // TODO
                }

            });
        }*/

    $('#wise-search-form-top').find('.alert').remove();
    $('#wise-search-form-top').append(
      '<div class="alert alert-danger alert-dismissible show" style="margin-top: 2rem;" role="alert">' +
        '  <strong>There was a error from the server.</strong> You should check in on some of those fields from the form.' +
        '  <button type="button" class="ui button close" data-dismiss="alert" aria-label="Close">' +
        '    <span aria-hidden="true">&times;</span>' +
        '  </button>' +
        '</div>',
    );

    // $(selectorFormContainer).find("[name='form.buttons.prev']").remove();
    // $(selectorFormContainer).find("[name='form.buttons.next']").remove();
    $('#form-widgets-marine_unit_id').prop('disabled', false);

    $('#wise-search-form-container-preloader').remove();
    $('#wise-search-form-preloader').remove();

    $('#ajax-spinner-form').hide();

    $("[name='form.buttons.prev']").prop('disabled', true);
    $("[name='form.buttons.next']").prop('disabled', true);

    $("[name='marine.buttons.prev']").prop('disabled', true);
    $("[name='marine.buttons.next']").prop('disabled', true);

    if (typeof Storage !== 'undefined') {
      sessionStore.removeItem('form');
    }

    loading = false;
  }

  function resetEmptyCheckboxes(fieldID) {
    $.each($('#' + fieldID).find('.option'), function (idx, item) {
      $(item).find("[type='checkbox']").prop('checked', true);
    });
  }

  function resetConfigsbelowFacet(
    called_from,
    called_from_button,
    called_from_select,
    args,
  ) {
    var empty_next_inputs;
    var empty_sibling_input;
    if (!called_from || called_from_button || called_from_select) {
      empty_next_inputs = function (el) {
        var panel_group, subform_parent, subform_children;
        panel_group = $(el).closest('.panel-group');
        subform_parent = panel_group.closest('.subform');
        subform_children = subform_parent.find('.subform');

        panel_group.nextAll('.panel-group').find('.panel').empty();
        if (subform_children.length) {
          if (subform_children.hasClass('subform')) {
            subform_children.empty();
          }
          subform_children.find('.panel').empty();
          subform_children.find('.subform').empty();
        } else {
          $(el).parent().parent().next().empty();
        }
      };

      empty_sibling_input = function (el) {
        var nextFieldID = $(el).parent().next().attr('id');

        var panel_group, subform_parent, subform_children;
        panel_group = $(el).closest('.panel-group');
        subform_parent = panel_group.closest('.subform');
        //subform_children = subform_parent.find('.subform');
        subform_children = $(el).parent().parent().next();

        if (
          called_from.from_marine_widget !== undefined ||
          called_from.from_marine_widget === true
        ) {
          return true;
        }

        if (nextFieldID === 'formfield-form-widgets-member_states') {
          resetEmptyCheckboxes(nextFieldID);
        } else {
          resetEmptyCheckboxes('memberstatesform');
        }
        panel_group.nextAll('.panel-group').find('.panel').empty();
        if (subform_children.length) {
          subform_children.find('.subform').empty();
        }
      };
      if (called_from_button) {
        empty_next_inputs(called_from_button);
      } else if (called_from_select) {
        empty_sibling_input(called_from_select);
      } else {
        $('.ui-autocomplete-input').each(function (idx, el) {
          if (el.value) {
            empty_next_inputs(el);
            return false;
          }
        });
      }
    }
  }

  function storageFactory(storage) {
    var inMemoryStorage = {};

    var length = 0;

    function isSupported() {
      try {
        var testKey = '__some_random_key_you_are_not_going_to_use__';
        storage.setItem(testKey, testKey);
        storage.removeItem(testKey);
        return true;
      } catch (e) {
        return false;
      }
    }

    function clear() {
      if (isSupported()) {
        storage.clear();
      } else {
        inMemoryStorage = {};
      }
    }

    function getItem(name) {
      if (isSupported()) {
        return storage.getItem(name);
      }
      if (inMemoryStorage.hasOwnProperty(name)) {
        return inMemoryStorage[name];
      }
      return null;
    }

    function key(index) {
      if (isSupported()) {
        return storage.key(index);
      } else {
        return Object.keys(inMemoryStorage)[index] || null;
      }
    }

    function removeItem(name) {
      if (isSupported()) {
        storage.removeItem(name);
      } else {
        delete inMemoryStorage[name];
      }
    }

    function setItem(name, value) {
      if (isSupported()) {
        storage.setItem(name, value);
      } else {
        inMemoryStorage[name] = String(value); // not everyone uses TypeScript
      }
    }
    return {
      getItem: getItem,
      setItem: setItem,
      removeItem: removeItem,
      clear: clear,
      key: key,
      length: length,
    };
  }

  function storeFormtoLocalStorage(options) {
    //var form =  $( selectorFormContainer ).find("form");

    //var strContent = $.getMultipartData("#" + form.attr("id"));
    var data = options.data || null;
    var boundary = options.boundary || null;
    var formData = options.formData || null;

    if (typeof LZString !== 'undefined') {
      var compressed = LZString.compressToEncodedURIComponent(data);
      var formD = LZString.compress(JSON.stringify(formData));

      if (typeof Storage !== 'undefined') {
        // We have local storage support
        sessionStore.setItem('form-' + defaultForm, compressed); // to save to local storage
        sessionStore.setItem('boundary', boundary);
        sessionStore.setItem(defaultForm, formD);
        // TODO: url shortner
        //window.location.hash = compressed;
      }
    }
  }

  function searchFormAjax(boundary, data, url, formData) {
    if (!url.includes('/marine/++api++')) {
      url = url.replace('/marine', '/marine/++api++');
    }

    $.ajax({
      type: 'POST',
      contentType: 'multipart/form-data; boundary=' + boundary,
      cache: false,
      data: data,
      dataType: 'html',
      url: url,
      //processData:false,
      beforeSend: beforeSendForm,
      success: function (dataRes, status, req) {
        /*function isnotchecked($field) {
                    var arr = [];
                    $.each( $field.find(".option input[type='checkbox']:not(:checked)") , function (ix, ch) {
                        arr.push( $(ch).parent() );
                    });
                    if(arr.length > 0){
                        return true;
                    }
                    return false;
                }
                var $fields = $( selectorFormContainer + ", " + selectorLeftForm ).find("[data-fieldname]");
                var cheked = false;

                $.each($fields,function (ix, $field) {
                    if(!isnotchecked($field)){
                        cheked = true;
                    }
                });

                if(cheked){
                    storeFormtoLocalStorage({ boundary: boundary,data: data, formData: formData});
                }*/

        storeFormtoLocalStorage({
          boundary: boundary,
          data: data,
          formData: formData,
        });

        formSuccess(dataRes, status, req);
      },
      complete: formAjaxComplete,
      error: formAjaxError,
    });
  }

  var defaultForm =
    window.location.pathname.substr(
      window.location.pathname.indexOf('@@'),
      window.location.pathname.length - 1,
    ) || 'defaultForm';

  function restoreFromSessionStorage() {
    if (sessionStore.getItem('form-' + defaultForm) === null) {
      return false;
    }
    if ('undefined' === typeof LZString) {
      console.error('LZString not found');
      return false;
    }

    try {
      //var dec = LZString.decompressFromEncodedURIComponent(sessionStore.form);
      var dec = LZString.decompressFromEncodedURIComponent(
        sessionStore.getItem('form-' + defaultForm),
      );

      var form = $(selectorFormContainer).find('form');

      var strContent = $.getMultipartData('#' + form.attr('id'));

      var compareVals = function (fromStorage, fromForm) {
        var notSame = false;

        try {
          var prelFromStorage = JSON.parse(fromStorage);

          $.each(Object.keys(prelFromStorage), function (ix, item) {
            var arr = prelFromStorage[item];

            //TODO: issue on some pages especially on pagination
            var res =
              typeof fromForm[item] !== 'undefined'
                ? fromForm[item].filter(function (el) {
                    return arr.indexOf(el) === -1;
                  })
                : [];
            if (res.length > 0) {
              notSame = true;
              return false;
            }
          });
        } catch (e) {
          return false;
        }

        if (!notSame) return false;

        return true;
      };

      var defForm = sessionStore.getItem(defaultForm);

      var getFormD = $.getMultipartData(
        '#' + form.attr('id'),
        sessionStore.getItem('boundary'),
      );

      if (compareVals(LZString.decompress(defForm), strContent[2])) {
        var url = form.attr('action');
        var boundary = sessionStore.getItem('boundary');

        searchFormAjax(boundary, dec, url);

        // TODO: url shortner
        //window.location.hash = sessionStore.getItem("form-" + defaultForm);
      } else {
        console.log('same data');
      }
    } catch (e) {
      console.log(e);
    }
  }

  function resetStorageForPage(ev) {
    var isLink = $(this).attr('href').indexOf('@@');
    var href = $(this).attr('href');
    if (isLink > 0) {
      ev.preventDefault();
      var ls = $(this)
        .attr('href')
        .substr(isLink, href.length - 1);
      sessionStore.removeItem(ls);
      sessionStore.removeItem('form');
      window.location.href = href;
    }
  }

  function removeNoValues() {
    /* Remove 'No value' options from all select elements
     */
    var $select = $('.select-widget');
    $select.find("option:contains('No value')").each(function () {
      $(this).remove();
    });
  }

  $.fn.fixTableHeaderAndCellsHeight = function () {
    // because the <th> are position: absolute, they don't get the height of
    // the <td> cells, and the other way around.

    this.each(function () {
      $('th', this).each(function () {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var cells_max_height = Math.max($next.height());
        var height = Math.max($th.height(), cells_max_height);

        $th.height(height);

        if ($th.height() >= cells_max_height) {
          $next.height($th.height());
        }

        $('div', this).css('margin-top', '-4px');
      });
    });
  };

  function fixTableHeaderAndCellsHeight() {
    var $table = $('.table-report');
    $table.fixTableHeaderAndCellsHeight();
  }

  function addDoubleScroll() {
    var secondScroll =
      '<div class="cloned-scroll-top" style="overflow-x: auto;">' +
      '<div style="height: 1px; margin-left: 165px;"></div>' +
      '</div>';

    $('.double-scroll').each(function () {
      var $doubleScroll = $(this);
      var $table = $doubleScroll.find('table');
      var tableWidth = $table.outerWidth((includeMargin = true));

      if (tableWidth == null || tableWidth <= $table.parent().width()) {
        return;
      }

      $doubleScroll.parent().before(secondScroll);
      var $clonedScrollTop = $doubleScroll
        .parent()
        .siblings('.cloned-scroll-top')
        .first();

      $clonedScrollTop.on('scroll', function () {
        $doubleScroll.scrollLeft($clonedScrollTop.scrollLeft());
      });

      $doubleScroll.scroll(function () {
        $clonedScrollTop.scrollLeft($doubleScroll.scrollLeft());
      });

      $clonedScrollTop.children().width(tableWidth);
    });
  }

  jQuery(document).ready(function ($) {
    window.setTimeout(function () {
      initPageElems();
    }, 100);

    var formAction = $('.wise-search-form-container form').attr('action') || '';
    if (formAction.includes('/marine/++api++')) {
      var newFormAction = formAction;
    } else {
      var newFormAction = formAction.replace('/marine', '/marine/++api++');
    }

    $('.wise-search-form-container form').attr('action', newFormAction);

    /*$(window).on("resize", function () {
            if (window.matchMedia("(max-width: 1024px)").matches) {
                /!*var el = $("#form-buttons-next-top");
                el.css("float","right");
                $("#form-buttons-prev-top").after(el);*!/

                /!*$("#marine-widget-top > div").css("display", "block");
                $("#marine-widget-top .field").css("display", "block");*!/
            }
        });*/

    var AJAX_MODE = true;

    window.WISE = {};
    window.WISE.formData = $(selectorFormContainer).clone(true);
    window.WISE.blocks = [];

    // ajax form submission
    $(selectorFormContainer)
      .unbind('click')
      .on('click', '.formControls #form-buttons-continue', function (ev) {
        if (!AJAX_MODE) {
          return true;
        }
        ev.preventDefault();

        // empty facets below given facet where we had an interaction
        // this way we reset the configurations below the given facet
        // with which we interacted with
        var called_from = arguments[1];
        var called_from_button = called_from && called_from['button'];
        var called_from_select = called_from && called_from['select'];

        var resetFacets = true;
        if (resetFacets) {
          resetConfigsbelowFacet(
            called_from,
            called_from_button,
            called_from_select,
            arguments,
          );
        }

        var form = $(selectorFormContainer).find('form');
        var url = form.attr('action');

        var strContent = $.getMultipartData('#' + form.attr('id'));

        searchFormAjax(strContent[0], strContent[1], url, strContent[2]);
      });

    restoreFromSessionStorage();

    $('.topnav a').on('click', resetStorageForPage);

    removeNoValues();
    fixTableHeaderAndCellsHeight();
    addDoubleScroll();
  });
})(window, document, jQuery);
