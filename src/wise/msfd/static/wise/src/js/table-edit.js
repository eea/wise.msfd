(function($){
  function setupEditRecommendationModal() {
    var $modal = $('#edit-recommendation');

    $modal.on('show.bs.modal', function(event){
      var $btn = $(event.relatedTarget);
      var cells = $btn.parent('td').parent('tr').children('td')

      // clear form
      $('#recomm-code').text('');
      $('#recomm-code').parent().removeClass('disabled');
      $('#recomm-code').removeClass('disabled');
      $('#recomm-text').text('');
      $('#topic option').each(function(){
        $(this).removeProp('selected');
      });
      $('#ms-region option').each(function(){
        $(this).removeProp('selected');
      });
      $('#descriptors option').each(function(){
        $(this).removeProp('selected');
      });

      // edit recommendation button pressed, prefill the form with values
      if (cells.length) {
        var rec_code = $(cells[0]).text();
        var topic = $(cells[1]).text();
        var recommText = $(cells[2]).text();
        var msRegion = $(cells[3]).text().split(',').map(function(item){ return item.trim(); });
        var descriptors = $(cells[4]).text().split(',').map(function(item){ return item.trim(); });

        $('#recomm-code').text(rec_code);
        $('#recomm-code').parent().addClass('disabled');
        $('#recomm-code').addClass('disabled');
        $('#recomm-text').text(recommText);

        $('#topic option').each(function(){
          var currentValue = this.value;

          if (topic == currentValue) {
            $(this).prop('selected', true);
          }
        });

        $('#ms-region option').each(function(){
          var currentValue = this.value;

          if (msRegion.includes(currentValue)) {
            $(this).prop('selected', true);
          }
        });

        $('#descriptors option').each(function(){
          var currentValue = this.value;

          if (descriptors.includes(currentValue)) {
            $(this).prop('selected', true);
          }
        });
      };

    });
  };

  function setupEditMSFDReportingHistoryModal() {
    var $modal = $('#edit-msfd-history');

    $modal.on('show.bs.modal', function(event){
      var $btn = $(event.relatedTarget);
      var cells = $btn.parent('td').parent('tr').children('td').not('.edit-row-button')

      var maxRows = $('#Row').attr('max-rows');
      $('#Row').text(maxRows)

      //clear form
      $(this).find('textarea.editable').each(function(){
        $(this).text('')
      });

      // edit recommendation button pressed, prefill the form with values
      if (cells.length) {
        cells.each(function(index){
          var text = $(this).text();
          var formTextareas = $modal.find('textarea');
          $(formTextareas[index]).text(text);
        });
      };
    });
  };

  $(document).ready(function() {
    setupEditRecommendationModal();
    setupEditMSFDReportingHistoryModal();
  });

}(jQuery));