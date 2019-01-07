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
  function setupRightSelects2(selector){
    var forbiddenIDs = [ ];
    var selectorFormCont = selector || selectorFormContainer;

    $( selectorFormCont + " select").each(function (ind, selectElement) {
      var selectedElementID = $(selectElement).attr("id");
      if( forbiddenIDs.indexOf(selectedElementID) !== -1 ){
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
      if(lessOptions) options.minimumResultsForSearch = Infinity;

      $(selectElement).select2(options);

    });
  }

  function initStyling(){
    //$("#form-buttons-continue").hide("fast");
    $(".button-field").addClass("btn");

    // mobile hide .toggle-sidebar
    $(".toggle-sidebar").hide();
  }

  function setupFormToggle(){
    var accordeons = $(".collapsed-container");

    $.each(accordeons , function(idx, accordion){
      var $accordion = $(accordion);
      var subforms = $accordion.find(".subform");

      if(subforms.length === 0){
        return false;
      }

      $accordion.prepend("<div class='collapsed-header' " +
        "data-toggle='collapse' data-target='#"+ "collapsed-container" + idx
        +"' >Show form</div>" );
      $accordion.append("<div id='"+ "collapsed-container" + idx +"' class='collapsed-content'></div>");
      $accordion.find(".collapsed-content").append(subforms);

      var $accHeader = $($accordion.find(".collapsed-header"));
      var $accContent = $($accordion.find(".collapsed-content"));

      var isCollapsed = function(){
        $accHeader
          .removeClass("form-collapsed")
          .text("Show form");
      };

      var notCollapsed = function(){
        $accHeader
          .addClass("form-collapsed")
          .text("Hide form");
      };

      $accHeader.on("click", function (ev) {
        $accContent.collapse();
      });

      $accContent.on("hidden.bs.collapse",function(){
        isCollapsed();
      });
      $accContent.on("show.bs.collapse",function(){
        notCollapsed();
      });
      $accContent.collapse('show');
    });
  }

  /*
   * CHECKBOXES functions
   * */
  function generateControlDiv(){
    var spAll = '<span class="controls" style="display: inline-block;background-color: #ddd;padding-top: 2px;padding-bottom: 2px;' +
      'padding-left: 0;position: relative;  ">' +
      '<span style="font-size: 0.8em; margin-left: 5px;">Select :</span><a class="" data-value="all"><label>' +
      '<span class="label">All</span></label></a>';
    var spClear = '<a class="" data-value="none" ><label><span class="label">Clear all</span></label></a>';
    var invertSel = '<a class="" data-value="invert"><label><span class="label">Invert selection</span></label></a>' +
      '<div class="btn btn-default apply-filters" data-value="apply"><span class="" >Apply filters</span></div>'+
      '<span class="ui-autocomplete">' +
      '<span class=" search-icon" ></span>' +
      '<span style="position: relative;padding-top:1px;padding-bottom:1px;background: white;" class="search-span">' +
      '<input class="ui-autocomplete-input" type="text" style="width: 80%;" />' +
      '<span class="clear-btn"><a class="fa fa-times"></a></span>' +
      '</span>' +
      '</span>';
    return spAll + spClear + invertSel;
  }

  function generateCheckboxes($fields, $fieldsnr){
    var count = $fieldsnr;
    $fields.each(function(indx, field){
      var $field = $(field);

      var cheks = $field.find(".option");
      var allcheckboxes = cheks.find("input[type='checkbox']");
      var hasChecks = allcheckboxes.length > 0;

      // has checkboxes
      if(hasChecks){
        var fieldId = $field.attr("id");
        /*$field.css({
                    "width" : "50%"
                });*/
        //fieldAutoSubmitSetup(fieldId, $field);

        // add "controls"
        var all = generateControlDiv();
        $field.find("> label.horizontal").after(all);

        //tooltips
        cheks.each(function (idx) {
          var text = $(cheks[idx]).text();
          $(cheks[idx]).attr("title", text.trim());
        });

        if(cheks.length < 4) {
          $field.find(".controls a").hide();
          $field.find(".controls").html("").css("height" ,"1px").css("padding", 0);
        } else {
          addCheckboxPanel($field, fieldId, cheks  );

          $field.find(".search-icon").on("click" , function (ev) {
            $(ev.target).parent().find("input").trigger("focus");
          });
        }

        sortCheckboxesByChecked($field);
      }

    });
  }

  function filterInvalidCheckboxes(cbxs){
    return cbxs.filter(function (idx, item) {
      return exceptVal.indexOf($(item).val()) === -1;
    });
  }

  function addCheckboxPanel($field, fieldId, cheks){
    $field.addClass("panel-group");

    var chekspan = $field.find("> span:not(.controls)");
    chekspan.css("border-radius", 0);
    chekspan
      .addClass( fieldId + "-collapse")
      .addClass("collapse")
      .addClass("panel")
      .addClass("panel-default");

    var label = $field.find(".horizontal");

    var alabel = "<a data-toggle='collapse' class='accordion-toggle' >" + label.text() + "</a>";
    label.html(alabel);

    label.addClass("panel-heading").addClass("panel-title");

    label.attr("data-toggle", "collapse");
    label.attr("data-target", "." + fieldId + "-collapse" );

    // if already checked than collapse
    // double collapse fix
    chekspan.collapse({ toggle: true });
    chekspan.collapse({ toggle: true });

    $field.find(".accordion-toggle").addClass("accordion-after");

    // hidden-colapse event
    chekspan.on("hidden.bs.collapse", function () {
      chekspan.fadeOut("fast");
      $field.find(".controls").slideUp("fast");
      $field.css({"border-bottom" : "1px solid #ccc;"});
    });

    // show accordion
    chekspan.on("show.bs.collapse", function () {
      // collapsed
      chekspan.fadeIn("fast");
      $field.find(".controls").slideDown("fast");
      $field.find("> span").css({"display" : "block"});
      $field.find(".accordion-toggle").addClass("accordion-after");
    });

    // hide accordion
    chekspan.on("hide.bs.collapse", function () {
      // not collapsed
      window.setTimeout( function (){
        $field.find(".accordion-toggle").removeClass("accordion-after");
      },600);
    });

    // initialize autocomplete for more than 6 checkboxes
    if(cheks.length < 6) {
      $field.find(".controls .ui-autocomplete").hide();
    } else {
      // 96264 save checked items when having search input in case the user
      // goes back on the search
      chekspan.append("<span class='noresults hidden'>No results found</span>");
      chekspan.data('checked_items', []);

      var data = chekspan.data('checked_items');
      $.each($field.find('input:checked'), function(idx, el){
        data.push(el.id);
      });

      addAutoComplete($field);
    }
  }

  function addAutoComplete($field){
    $field.find(".ui-autocomplete-input").autocomplete({
      minLength: 0,
      source: [],
      search: function(event){
        searchAutoComplete(event.target, $field);
      },
      create: function (){
        var that = this;
        var removeBtn = $(this).parentsUntil(".ui-autocomplete").find(".clear-btn ");
        removeBtn.on("click", null ,  that, function (ev) {
          $(this).parentsUntil(".controls").find("input").val("");
          $(this).parentsUntil(".controls").find("input").trigger("change");
          $(ev.data).autocomplete("search","undefined");
        });
      }
    });
  }

  function searchAutoComplete(evtarget, $field){
    var cheks2 = $field.find(".option .label:not(.horizontal) ");
    var labels = cheks2.parentsUntil(".option").parent();
    var inputs = labels.find('input');
    var options = labels.parent();
    var no_results = options.find(".noresults");

    if( $(evtarget).val() === "" ){
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

    $field.find(".apply-filters").show();
    //$(evtarget).find(".apply-filters").show();
    labels.removeClass('hidden');

    var toSearch = $( evtarget ).val().toLowerCase().replace(/\s/g, "_");

    var matcher = new RegExp( $.ui.autocomplete.escapeRegex( toSearch ), "i" );

    var temp = {};
    var checksLabels = $field.find(".option .label:not(.horizontal) ").map(function (ind, item) {
      temp[$(item).text().toLowerCase()] = $(item).text().toLowerCase()
        .replace(/\s/g, "_");
      //return temp;
      return $(item).text().toLowerCase()
      /*.replace(/^\s+|\s+$/g, '')*/
      /*.replace(/_/g, "")*/
        .replace(/\s/g, "_");
    });

    var found = [];
    $.each(temp, function (indx, item) {
      if(!matcher.test( item )){
        found.push(indx);
      }
    });

    var tohide = cheks2.filter(function (idx, elem) {
      return found.indexOf( $(elem).text().toLowerCase()) !== -1;
    });

    var toshow =  cheks2.filter(function (idx, elem) {
      return found.indexOf( $(elem).text().toLowerCase()) === -1;
    });
    $.each(toshow, function (ind, item) {
      $(item).parentsUntil(".option").parent().find("[type='checkbox']").prop("checked", true);
    });

    $.each(tohide, function (inx, item) {
      $(item).parentsUntil(".option").parent().find("[type='checkbox']").prop("checked", false);
      $(item).parentsUntil(".option").parent().find("input[type='checkbox']").prop("checked", false);
      $(item).parentsUntil(".option").parent().find("input[type='checkbox']").removeAttr('checked');
      $(item).parentsUntil(".option").parent().addClass('hidden');
    });

    if(tohide.length === cheks2.length) {
      no_results.removeClass('hidden');
    }
    else {
      no_results.addClass('hidden');
    }
  }

  function sortCheckboxesByChecked($field) {
    if ( window.WISE !== undefined && window.WISE.blocks !== undefined && window.WISE.blocks.indexOf( $field.attr("id") ) !== -1 ){
      return;
    }
    var arr = [];
    $.each( $field.find(".option input[type='checkbox']:not(:checked)") , function (ix, ch) {
      arr.push( $(ch).parent() );
    });
    var found = $field.find(".option input[type='checkbox']:checked");
    var foundArr = [];
    if(found.length > 0){
      $.each(found, function (ix, item) {
        foundArr.push($(item).parent() );
      });
    }
    var all = foundArr.concat(arr);

    $.each( all, function (ix, ch) {
      $field.find(".panel").append(ch);
    });
  }

  function checkboxHandlerAll(ev){
    ev.preventDefault();

    var par = $(this).parent().parent();

    //window.WISE.blocks.push( $(this).parentsUntil(".field").parent().attr("id") );

    par.find(".apply-filters").show();
    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    $.each(rest, function (idx) {
      if($(rest[idx]).val() !== "all" && $(rest[idx]).val() !== "none") $(rest[idx]).prop("checked", true);
    });

    //$( selectorFormContainer + " .formControls #form-buttons-continue").trigger("click");
  }

  function checkboxHandlerNone(ev){
    ev.preventDefault();

    $(this).prop("checked", false);
    var par = $(this).parent().parent();
    par.find(".apply-filters").show();
    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    //window.WISE.blocks.push( $(this).parentsUntil(".field").parent().attr("id") );

    $.each(rest, function (idx) {
      $(rest[idx]).prop("checked", false);
      //if( $(rest[idx]).val() !== "none")
    });

    //$( selectorFormContainer + " .formControls #form-buttons-continue").trigger("click");
  }

  function checkboxHandlerInvert(ev){
    ev.preventDefault();
    $(this).prop("checked", false);

    var par = $(this).parent().parent();
    par.find(".apply-filters").show();

    //window.WISE.blocks.push( $(this).parentsUntil(".field").parent().attr("id") );

    var rest = filterInvalidCheckboxes($(par).find("[type='checkbox']"));

    var checked = rest.filter(function (ind, item) {
      return $(item).is(":checked");
    });

    var unchecked = rest.filter(function (ind, item) {
      return !$(item).is(":checked");
    });

    $.each(checked, function (idx) {
      $(checked[idx]).prop("checked", false);
    });

    $.each(unchecked, function (idx) {
      $(unchecked[idx]).prop("checked", true);
    });
    //$( selectorFormContainer + " .formControls #form-buttons-continue").trigger("click");
  }

  function addCheckboxHandlers(){
    var $controls = $(".controls");
    $controls.on("click","a[data-value='all']", checkboxHandlerAll);
    $controls.on("click", "a[data-value='none']", checkboxHandlerNone);
    $controls.on("click", "a[data-value='invert']", checkboxHandlerInvert);
    //$(".controls .apply-filters").on("click", $( selectorFormContainer + " .formControls #form-buttons-continue").trigger("click") );

    $controls.one("click",".apply-filters", function () {
      $(selectorFormContainer + " [name='form.widgets.page']").val(0);
      $(selectorFormContainer + " .formControls #form-buttons-continue").trigger("click", {'button': this});
    });
  }

  function addCheckboxLabelHandlers(){
    var allch = $( "#comp-national-descriptor" ).find("[data-fieldname]");

    var triggerClick = function (chV, ev){
      //reset page
      $(selectorFormContainer + " [name='form.widgets.page']").val(0);
      if( exceptVal.indexOf(chV) === -1) $(ev.target).find("input[type='checkbox']").trigger('click');
    };

    // listener for click on the whole span
    allch.on("click", ".option", function(ev){
      $("#ajax-spinner2").hide();
      var checkboxV = $(this).find("input[type='checkbox']").val();
      if( window.WISE.blocks.indexOf( $(this).parentsUntil(".field").parent().attr("id") ) !== -1  ){
        //return false;
      } else {
        //triggerClick(checkboxV, ev);
      }
    });
  }


  $.fn.fixTableHeaderHeight = function fixTableHeaderHeight() {
    // because the <th> are position: absolute, they don't get the height of
    // the <td> cells, and the other way around.
    this.each(function() {

      $("th", this).each(function() {
        var $th = $(this);
        var $next = $('td', $th.parent());
        var thh = Math.max($next.height());
        var mh = Math.max($th.height(), thh);

        // console.log("TH", $th, thh, mh)

        $th.height(mh - 1);
        $next.height(mh);
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

  };

  $.fn.toggleTable = function toggleTable(onoff) {
    var original = $(this).data('original');
    if (onoff) {
      $(this).simplifyTable();
    } else {
      $(this).html(original);
      $(this).fixTableHeaderHeight();
      addTranslateClickHandlers();
    }
  };

  $(document).ready(function($){
    initStyling();

    var $fields = $("[data-fieldname]");
    if($fields.length > 0){
      generateCheckboxes( $fields, $fields.length );
    }

    addCheckboxHandlers( $("#comp-national-descriptor") );

    addCheckboxLabelHandlers();

    setupRightSelects2();

    if (window.matchMedia("(max-width: 768px)").matches) {
      $(".overflow-table h5").width( $(".overflow-table table").width() );
    }

    //$('.simplify-form').next().find('table').simplifyTable();
    $('.simplify-form').next().find('table').each(function(){
    	$(this).simplifyTable();
    });

    $('.simplify-form button').on('click', function(){
      var onoff = $(this).attr('aria-pressed') == 'true';
      $p = $(this).parent().next();
      $('table', $p).toggleTable(!onoff);
    });
  });
}(window, document, $));
