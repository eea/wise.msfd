// Collapse navigation and move search section
// when it's running out of space in the header
function autoCollapseNavigation() {
  var $header = $("#content-header");
  var $navbar = $(".navbar-nav");
  var $searchSubmitButton = $(".search-submit");

  $header.removeClass("collapse-nav");
  if ($navbar.innerHeight() > 65) {
    $header.addClass("collapse-nav");
    // Move search and login to navbar container
    $(".top-actions").prependTo(".navbar-collapse");
  } else {
    $(".top-actions").prependTo(".right-actions-section");
  }

  // sticky menu
  $(function() {
    var div = $("#portal-top");
    var isNavCollapsed = $(".collapse-nav").length > 0;

    $(window).on("scroll touchmove", function() {
      if (isNavCollapsed) {
        var scroll = $(window).scrollTop();
        div.toggleClass("sticky-header", scroll >= 100);
      } else {
        div.removeClass("sticky-header");
      }
    });
  });
}

// Align submenu to the right
// if overflows the main navigation menu
function alignNavSubmenu() {
  var $header = $("#portal-top");
  var $nav = $("#portal-globalnav");
  var $navItems = $nav.children("li");
  var mainMenuWidth = $header.width();
  $navItems.mouseenter(function() {
    var $this = $(this);
    var $submenu = $this.children(".submenu");
    var subMenuWidth = $submenu.width();

    if ($submenu.length > 0) {
      var subMenuLeftPos = $submenu.offset().left;
    }

    if (mainMenuWidth - (subMenuWidth + subMenuLeftPos) < 0) {
      $submenu.addClass("aligned-submenu");
    }
  });
}

function displayImageCaption() {
  var $img = $("#content-core p").find("img");
  $img.each(function() {
    var $this = $(this);
    var imgWithSource = !$this.attr("title").match(/png|jpg/g);
    var imgClass = $this.attr("class");

    if (imgWithSource) {
      $this.wrap('<div class="image-wrapper" />');
      $this.after('<p class="image-caption">' + $(this).attr("title") + "</p>");
      $this.parent(".image-wrapper").addClass(imgClass);
      $this.siblings(".image-caption").css("width", $this.width());
    }
  });
}

function collapsibleContent() {
  var $readMoreBtn = $(".read-more-btn");
  if ($readMoreBtn.length > 0) {
    $readMoreBtn.each(function() {
      var $this = $(this);
      $this.closest("table").addClass("collapse-wrapper");
      $this
        .parent()
        .siblings()
        .wrapAll('<div class="collapse-content"/>');
      var collapsibleContent = $this.parent().siblings(".collapse-content");

      $('<div class="collapse-layer fadein"/>').prependTo(collapsibleContent);

      $this.click(function() {
        var $btn = $(this);
        collapsibleContent
          .toggleClass("in")
          .find(".collapse-layer")
          .toggleClass("fadein");

        $btn.toggleClass("arrow-up").text(function(a, b) {
          return b == "Read more" ? "Read less" : "Read more";
        });
      });
    });
  }
}

// function openSubmenuOnClick() {
//   var $submenuItem = $('#portal-globalnav a');
//   $submenuItem.each(function() {
//     var $this = $(this);
//     // if ($this.siblings().hasClass('expand-dropdown')) {
//     //   $this.find('.sm-caret').removeClass('sm-caret-up').addClass('sm-caret-down');
//     // }
//
//     $this.click(function() {
//       var $a = $(this);
//       // if (!$a.siblings().hasClass('expand-dropdown')) {
//       //   $a.find('.sm-caret').toggleClass('sm-caret-up sm-caret-down');
//       // }
//       $a.siblings('.dropdown-menu').toggle();
//     });
//   });
// }

// HOMEPAGE key messages section
function keyMessagesTabFunctionality() {
  var $tabNavItem = $(".fp-nav-tabs li");

  $tabNavItem.click(function() {
    var $this = $(this);
    var tab_id = $this.attr("data-tab");

    $tabNavItem.removeClass("current");
    $(".fp-tab-content").removeClass("current");

    $this.addClass("current");
    $("#" + tab_id).addClass("current");
  });
}

function setKeyMessagesCardsHeight() {
  // Get the heighest div and make equal height on every cards
  var $tab = $(".fp-tab-content");
  var maxHeight = 0;

  $tab.each(function() {
    var $card = $(this).find(".tab-card-content");
    $card.each(function() {
      var $this = $(this);
      maxHeight =
        $this.outerHeight() > maxHeight ? $this.outerHeight() : maxHeight;
    });
    $card.closest(".fp-tab-card").css("height", maxHeight);
  });
}

function initKeyMessageSlider() {
  var $tabSlider = $(".fp-tab-slider");
  $tabSlider.each(function(index, element) {
    var $slider = $(this);

    $slider
      .on("init", function() {
        $(".spinner-wrapper").hide();
      })
      .slick({
        dots: true,
        speed: 300,
        infinite: false,
        slidesToShow: 3,
        slidesToScroll: 3,
        lazyLoad: "progressive",
        responsive: [
          {
            breakpoint: 1060,
            settings: {
              slidesToShow: 2,
              slidesToScroll: 2
            }
          },
          {
            breakpoint: 650,
            settings: {
              slidesToShow: 1,
              slidesToScroll: 1
            }
          }
        ]
      });
  });
}

function initHomepageSlider() {
  var $slider = $("#slideshow");
  $slider.slick({
    infinite: true,
    speed: 500,
    fade: true,
    slidesToShow: 1,
    autoplay: true,
    autoplaySpeed: 4000,
    prevArrow: $(".slide-prev"),
    nextArrow: $(".slide-next")
  });
}

function countryProfileSideBar() {
  $(window)
    .scroll(function() {
      var $countryContent = $(".country-content");
      if ($countryContent.length) {
        var contentPos = $countryContent.offset().top;
        var scrollDistance = $(window).scrollTop() - contentPos;
        $(".country-dashboard-section").each(function(i) {
          var posTop = $(this).position().top;
          if (posTop <= scrollDistance) {
            $(".autotoc-nav a.active").removeClass("active");
            $(".autotoc-nav a")
              .eq(i)
              .addClass("active");
          }
        });
      }
    })
    .scroll();
}

function customCountrySelectDropdown() {
  $(".dd-select").click(function(e) {
    $(".dd-select-list").toggle();
    e.preventDefault();
  });

  $(".dd-country").click(function() {
    $(".dd-select-list").hide();
    var url = $(this).data("value");
    document.location = url;
  });
}

function initThumbnailForDashboards() {
  if ($("#country-factsheet").length === 0) {
    $("iframe").each(function() {
      var $this = $(this);
      var iframeSRC = $this.attr("src");
      
      if(iframeSRC){
        var isTableauDashboard = /tableau/i.test(iframeSRC);
      } else {
        var isTableauDashboard = false;
      }

      if (isTableauDashboard) {
        $('<img class="tableau-thumb"/>').insertAfter($this);
        var $thumb = $this.siblings(".tableau-thumb");
        var thumbSRC = iframeSRC + "&:format=png";
        $thumb.attr("src", thumbSRC);
        $this.addClass("tableau-vis");
      }
    });
  }
}

function initDashboardsToolbar() {
  $("iframe").each(function(i) {
    var $iframe = $(this);
    var iframeSRC = $iframe.attr("src");
    
    if(iframeSRC){
      var isTableauDashboard = /tableau/i.test(iframeSRC);
    } else {
      var isTableauDashboard = false;
    }
    

    // Copy tableau dashboard link
    function setupShareButton() {
      var pathArray = iframeSRC.split("/");
      var t_siteRoot = "/" + pathArray[3] + "/" + pathArray[4];
      
      if(pathArray.length == 6) {
        // https://tableau-public.discomap.eea.europa.eu/views/BathingWaterQuality_Marine_Country_profile_2020_16431054968230/Country?P_Country=Croatia
        var t_name = pathArray[4] + "/" + pathArray[5].split("?")[0];
        var t_filter = pathArray[5].split("?")[1];
      } else {
        // https://tableau.discomap.eea.europa.eu/t/Wateronline/views/GESassessments_CountryProfiles/CountryProfiles?Country=Croatia
        var t_name = pathArray[6] + "/" + pathArray[7].split("?")[0];
        var t_filter = pathArray[7].split("?")[1];
      }

      t_filter = t_filter.split("&:")[0];
      
      var embed =
        "<script type='text/javascript'" +
        "src='https://tableau.discomap.eea.europa.eu/javascripts/api/viz_v1.js'></script>" +
        "<div class='tableauPlaceholder' style='width: 100%; height: 850px;'>" +
        "<object class='tableauViz' width='100%' height='850' style='display:none;'>" +
        "<param name='host_url' value='https%3A%2F%2Ftableau.discomap.eea.europa.eu%2F' />" +
        "<param name='site_root' value='" +
        t_siteRoot +
        "' />" +
        "<param name='name' value='" +
        t_name +
        "' />" +
        "<param name='filter' value='" +
        t_filter +
        "'/>" +
        "<param name='toolbar' value='no' />" +
        "<param name='isGuestRedirectFromVizportal' value='y' />" +
        "</object>" +
        "</div>";

      var $copyLinkButton = $(".copy-btn", $toolbar);
      var $copyEmbedButton = $(".copy-embed", $toolbar);
      var $closeDialog = $(".close-dialog", $toolbar);
      var $shareButton = $(".cl-button", $toolbar);
      var $dialog = $(".share-dialog", $toolbar);
      var $textarea = $("textarea", $toolbar);
      var $input = $(".copy-link-input", $toolbar);
      var $tabNavItem = $(".daviz-nav-tabs", $toolbar).children("li");

      $textarea.val(embed);
      $copyLinkButton.attr("data-clipboard-text", iframeSRC);
      $copyEmbedButton.attr("data-clipboard-text", embed);
      // $(".copy-link-input").attr("value", iframeSRC);
      $input.attr("value", iframeSRC);

      $tabNavItem.click(function() {
        var $this = $(this);
        var tab_id = $this.attr("data-tab");

        $tabNavItem.removeClass("current");
        $this
          .parent()
          .siblings(".daviz-tab-content")
          .removeClass("current");
        $this.addClass("current");
        $this
          .parent()
          .siblings("#" + tab_id)
          .addClass("current");
      });

      $shareButton.click(function() {
        $dialog.show();
      });

      $closeDialog.click(function() {
        $dialog.hide();
      });

      $textarea.on("click", function() {
        this.select();
      });

      $input.on("click", function() {
        this.select();
      });

      var clipboard = new ClipboardJS(".dialog-btn");
      clipboard.on("success", function(e) {
        e.clearSelection();
        e.trigger.textContent = "Copied to clipboard!";
        e.trigger.style.backgroundColor = "#269b65";
        window.setTimeout(function() {
          if (e.trigger.className.indexOf("copy-embed") !== -1) {
            e.trigger.textContent = "Copy embed code";
          } else {
            e.trigger.textContent = "Copy sharing URL";
          }
          e.trigger.style.backgroundColor = "#005588";
        }, 2000);
      });

      clipboard.on("error", function(e) {
        console.log("Trigger:", e.trigger);
      });
    }

    // Open tableau dashboard in the browser's fullscreen viewing mode
    function setupFullScreenMode() {
      i += 1;
      id = "section-" + i;
      $iframeWrapper.attr("id", id);

      var exitfullScreenButton =
        '<div class="toolbar-button close-fs-button" title="Exit Full Screen">' +
        '<i class="glyphicon glyphicon-remove"></i>' +
        "</div>";

      $(exitfullScreenButton).appendTo($iframeWrapper);
      var $goFullScreen = $(".fs-button", $toolbar);
      var $exitFullScreen = $(".close-fs-button", $iframeWrapper);

      var dashboard = document.getElementById(id);

      $goFullScreen.on("click", function() {
        if (dashboard.requestFullscreen) {
          dashboard.requestFullscreen();
        } else if (dashboard.msRequestFullscreen) {
          // IE/Edge
          dashboard.msRequestFullscreen();
        } else if (dashboard.mozRequestFullScreen) {
          // Firefox
          dashboard.mozRequestFullScreen();
        } else if (dashboard.webkitRequestFullScreen) {
          //Chrome, Safari & Opera
          dashboard.webkitRequestFullScreen();
        } else {
          alert(
            "Sorry, but Fullscreen API is not supported by your browser. " +
              "Please consider upgrading to the latest version " +
              "or use either Google Chrome or Mozilla Firefox for full support."
          );
        }
      });

      $exitFullScreen.on("click", function() {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.mozCancelFullScreen) document.mozCancelFullScreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
        else if (document.msExitFullscreen)
          window.top.document.msExitFullscreen();
      });
    }

    if (isTableauDashboard) {
      $iframe.addClass("wm-tableau");
      $iframe.wrap('<div class="iframe-wrapper"/>');
      var $iframeWrapper = $iframe.parent(".iframe-wrapper");
      $iframeWrapper.parent().css("position", "relative");

      $(".daviz-toolbar-container")
        .children(".dashboard-toolbar")
        .clone()
        .insertAfter($iframeWrapper);

      var $toolbar = $iframeWrapper.siblings(".dataviz-toolbar");

      setupFullScreenMode();
      if(iframeSRC){
        setupShareButton();
      }
    }
  });
}

function initReadEEAContent() {
  var $input = $("#form-widgets-ICatalogueMetadata-original_source");

  var $btn = $("<button>Fetch remote data</button>").on("click", function() {
    $btn.html("Fetching data...");
    $btn.attr("disabled", true);

    console.log("click");
    var val = $input.val();
    if (val && val.indexOf("www.eea.europa.eu") > -1) {
      $.get("./@@external_proxy", { url: val }, function(data) {
        console.log("data", data);
        $("#form-widgets-IDublinCore-title").val(data.title);
        $("#form-widgets-IDublinCore-description").html(
          (data.description && data.description.data) || ""
        );
        $btn.html("Fetch remote data");
        $btn.attr("disabled", false);
      });
    }
    return false;
  });

  $input.parent().append($btn);
}

$(document).ready(function() {
  var $window = $(window);
  // are dropdown, nu are default page: not clickable
  // are dropdown, are default page: clickable

  // Main navigation menu:
  // if item (folder) has not set a default page
  // prevent default link behavior on click
  $(".is-not-dp > a, #portal-globalnav>li>ul .hasDropDown").click(function(e) {
    if (
      $(this)
        .siblings()
        .hasClass("expand-dropdown")
    ) {
      return true;
    }
    e.preventDefault();
  });

  $("#main-container").css("visibility", "visible");

  // Top search modal
  $(".search-icon").click(function(e) {
    $(".search-modal").fadeToggle("fast");
    e.stopPropagation();
  });

  $(".search-modal").click(function(e) {
    e.stopPropagation();
  });

  $(".user-icon").click(function(e) {
    $(this)
      .siblings("#personal-bar-container")
      .fadeToggle("fast");
    e.stopPropagation();
  });

  $(function() {
    var $navItem = $("#portal-globalnav>li");
    var $frontPage = $(".section-front-page");
    if (!$frontPage.length) {
      $navItem.each(function() {
        var $this = $(this);
        $this.addClass("nav-separator");
        $this
          .mouseenter(function() {
            $(this)
              .removeClass("nav-separator")
              .next()
              .removeClass("nav-separator");
          })
          .mouseleave(function() {
            $(this)
              .addClass("nav-separator")
              .next()
              .addClass("nav-separator");
          });
      });
    }
  });

  $(function() {
    var $bottomLinks = $(".bottom-links");
    var linkItem = $bottomLinks.find("ul li");
    if ($bottomLinks.length > 0) {
      $bottomLinks
        .parent("#viewlet-below-content")
        .addClass("bottom-links-wrapper");
      linkItem.each(function() {
        var $this = $(this);
        if ($this.children("a").length > 0) {
          $this.addClass("has-link");
        }
      });
    }
  });

  autoCollapseNavigation();
  alignNavSubmenu();
  collapsibleContent();
  // openSubmenuOnClick();
  countryProfileSideBar();
  customCountrySelectDropdown();

  initReadEEAContent();

  $window.on("load", function() {
    displayImageCaption();
    initKeyMessageSlider();
    keyMessagesTabFunctionality();
    setKeyMessagesCardsHeight();
    initHomepageSlider();
    initThumbnailForDashboards();
    initDashboardsToolbar();
  });

  if ($("#country-factsheet").length > 0) {
    // move print button on country profile pages under header
    $("#print-button").insertAfter(".country-title");
  }

  var resizeTimer;
  $window.on("resize", function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(doneResizing, 100);
  });

  function doneResizing() {
    autoCollapseNavigation();
    setKeyMessagesCardsHeight();
  }
});

$(document).bind("click", function(e) {
  var $clicked = $(e.target);
  if (!$clicked.parents().hasClass("countries-dropdown")) {
    $(".dd-select-list").hide();
  }
  $(".search-modal").hide();
  $(".user-actions")
    .find("#personal-bar-container")
    .hide();
});
