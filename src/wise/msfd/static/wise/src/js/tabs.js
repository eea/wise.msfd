/* global setupTabs, clickFirstTab */

function clickFirstTab(){
    //$("#mainform-tabs ul li:first-child a").trigger('click');
    $("#tabs-wrapper ul li:first-child a").trigger('click');
    $(".tabs-wrapper ul li:first-child a").trigger('click');
}

window.setupTabs = function (tabswrapper) {
    function setupInnerTabs(tabsW) {
        var t = $("ul.nav:not(.topnav) > li");
        // tabs width calculation
        var nrtabs = t.length;
        if(nrtabs > 1) {
            var tabLength = nrtabs === 2 ? 35 : Math.floor((100 - nrtabs) / nrtabs );

            t.css("width", tabLength + "%");
            var rest = 100 - tabLength * nrtabs;

            var totalL = $("ul.nav").width();
            var mrR = Math.floor( totalL /100 );

            $(t).css({
                "margin-left": 0,
                "margin-right" : mrR/2 + "px"
            });

        } else {
            $(t).css({"margin-left": 0});
        }

        /*$.each( $( ".tabs-wrapper") , function (indx, item) {
            if($(item).find("ul").length ===  0){ return true;}
            //if($(item).find("ul li").length === 0) $(".tabs-wrapper").hide();
        });*/
    }

    function setupTopTabs(tabswrapper) {
        var tabsWrapper = tabswrapper || "#mainform-tabs";

        /* david commented
        if ($("#tabs-wrapper ul").find("li").length === 0){
            if( $("#tabs-wrapper").find("ul").length ===  0 ){ //return true;
            }
            //if($("#tabs-wrapper").find("ul li").length === 0) $("#tabs-wrapper").hide();
        } */

        var renderTopTabs = function () {
            var nrTabs = $( tabsWrapper + " ul.topnav li").length || 0;

            if (nrTabs === 0) {
              return false;
            }

            var PERCENT = false;

            if(PERCENT) {
                var totalLength = 100;
                var tabSpaces  = nrTabs - 1;
                var tabWidth = (totalLength - tabSpaces) / nrTabs ;
                var rest = totalLength - (tabWidth * nrTabs);
                var tabSpace = rest / (nrTabs-1);
                /*$( ".topnav li").css({
                    "width": tabWidth  + "%",
                    "margin-right": tabSpace + "%"
                });
                $( ".topnav li:last-child").css({
                   "margin-right" : "0"
                });*/
            } else {
                var totalLength = $( tabsWrapper + " ul.topnav").outerWidth();
                var tabSpaceWidth = 10;
                var tabSpaces = (nrTabs - 1)*tabSpaceWidth;
                var tabWidth = (totalLength - tabSpaces) / nrTabs ;
                var rest = totalLength - (tabWidth * nrTabs);
                var tabSpace = rest / (nrTabs-1);

                $( ".topnav li").css({
                    "width": tabWidth  + "px",
                    "margin-right": tabSpace + "px"
                });
                $( ".topnav li:last-child").css({
                   "margin-right" : "0"
                });
                $( ".topnav li.manage-users").css({
                    "width": "initial",
                });
            }
        };

        if( $( tabsWrapper + " ul li").length === 1 ){
            $("#tabContents").removeClass("tab-content");
            $( tabsWrapper + " ul").attr("class", "");
            $( tabsWrapper + " ul li").css({
                "background-color": "transparent",
                "float" : "none"
            });
            var lt = $( tabsWrapper + " ul li a").text();
            $( tabsWrapper + " ul li").append("<h4>" + lt + "</h4>");
            $( tabsWrapper + " ul li a").remove();
            $( tabsWrapper + " .tab-pane").removeClass("fade");
        }
        renderTopTabs();
    }

    // Krisz: disabled, TODO: make sure if we really need it
    // we can use flex to set equal width & height for tab items
    // setupTopTabs(tabswrapper);
    // setupInnerTabs(tabswrapper);

    clickFirstTab();
}

jQuery(document).ready(function($) {
    if ("undefined" !== typeof window.setupTabs) {
      window.setupTabs();
    }

    // var w = "auto";
    // var daw = true;
    //
    // function formatArticle (article) {
    //   var el = $(article.element[0]);
    //   var subtitle = el.attr("data-subtitle");
    //
    //   return '<span style="font-weight: bold;">' +
    //             el.attr("data-maintitle") + ': ' +
    //           '</span>' +
    //           '<span>'+ subtitle +'</span>';
    // }
    //
    // function marineUnitSelect(w,daw) {
    //   var $selectArticle = $("#mobile-select-article");
    //
    //   w = false;
    //   daw = false;
    //   var moptions = {
    //     placeholder: 'Select an option',
    //     closeOnSelect: true,
    //     dropdownAutoWidth: daw,
    //     width: w,
    //     theme: "flat",
    //     minimumResultsForSearch: 20,
    //     formatSelection: formatArticle,
    //     formatResult: formatArticle,
    //     containerCssClass: "mobile-select-article"
    //   };
    //
    //   if ($.fn.select2 !== undefined) {
    //     $selectArticle.select2(moptions);
    //     $selectArticle.one("select2-selecting", function (ev) {
    //       document.location.href = ev.choice.id;
    //     });
    //   }
    // }

    // marineUnitSelect(w,daw);

    $(window).on('resize', function(){
      // marineUnitSelect(w,daw);
      if ("undefined" !== typeof window.setupTabs) {
        window.setupTabs();
      }
    });

});
