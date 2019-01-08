if (!Array.prototype.last){
  Array.prototype.last = function(){
    return this[this.length - 1];
  };
};

(function(window, document, $){

  function initStyling(){
    // TODO: is this still needed? I don't think so
    //$("#form-buttons-continue").hide("fast");
    $(".button-field").addClass("btn");

    // mobile hide .toggle-sidebar
    $(".toggle-sidebar").hide();
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

    if (window.matchMedia("(max-width: 768px)").matches) {
      $(".overflow-table h5").width( $(".overflow-table table").width() );
    }

    $('.simplify-form').next().find('table').simplifyTable();

    // // tibi
    // $('.simplify-form').next().find('table').each(function(){
    //   $(this).simplifyTable();
    // });

    $('.simplify-form button').on('click', function(){
      var onoff = $(this).attr('aria-pressed') == 'true';
      $p = $(this).parent().next();
      $('table', $p).toggleTable(!onoff);
    });
  });
}(window, document, $));
