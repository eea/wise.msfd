(function(window, document, $){
  function makeSelect(parent, data, title) {
    $d = $("<div>");
    $d.append($("<label>").text(title));
    $select = $("<select>");
    $(data).each(function(){
      var $opt = $("<option>")
        .attr('value', this.u)
        .text(this.t)
        .data('data', this);
      ;
      $select.append($opt);
    });
    $d.append($select);
    parent.append($d);
    return $select;
  }

  function getChild(data, childName) {
    var res = null;
    $(data).each(function(){
      if (this.i == childName) {
        res = this;
      }
    });
    return res;
  }

  function setupNavigation(data) {
    var countries = getChild(data, 'national-descriptors-assessments')['c'];
    var $parent = $('#compliance-nav');
    makeSelect($parent, countries, 'Countries', function(){});
    makeSelect($parent, countries[0].c, 'Regions', function(){});
    makeSelect($parent, countries[0].c[0].c, 'Descriptors', function(){});
    makeSelect($parent, countries[0].c[0].c[0].c, 'Articles', function(){});
    makeSelect($parent, [
      {t: '2012', u: ''},
      {t: '2018', u:''}
    ], 'Version', function(){});
  }

  $(document).ready(function($){
    console.log(window.jsonMapURL);
    $.getJSON(window.jsonMapURL, setupNavigation);
  });

}(window, document, jQuery));
