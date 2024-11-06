require([
  'esri/Map',
  'esri/views/MapView',
  'esri/widgets/Home',
  'esri/layers/MapImageLayer',
  'esri/geometry/Extent',
  'esri/views/layers/support/FeatureFilter',
  'esri/layers/FeatureLayer',
  'dojo/domReady!',
], function(Map, MapView, Home, MapImageLayer, Extent, FeatureFilter, FeatureLayer) {

  // let filterLayerView;
  let focusExtent = new Extent(window.focusExtent);

  let layer = new FeatureLayer({
    url: window.layerUrl
  });
  let filter = new FeatureFilter({
    where: "Country = '" + window.focusCountry + "'",
  });

  const map = new Map({
    basemap: window.focusMapLayer || 'hybrid', //"gray-vector",
    layers: [layer]
  });

  var view = new MapView({
    map: map,
    container: "viewDiv",
    extent: focusExtent
  });
  view.filter = {
      where: "COUNTRY = '" + window.focusCountry + "'",
  };

  view.whenLayerView(layer).then(function(layerView) {
    console.log('whenLayerView', layerView);

    layerView.filter = {
      where: "Country = '" + window.focusCountry + "'"
    };

    // layerView.watch("updating", function(val) {
    //   console.log('updating', val);
    //
    //   // view.goTo(response.extent);
    //
    //   if (!val) {
    //     layerView.queryExtent().then(function(response) {
    //       // go to the extent of all the graphics in the layer view
    //       console.log('got extent', response.extent);
    //       if (response.extent) view.goTo(response.extent);
    //       // view.goTo(extent);
    //     });
    //   }
    // });
  });


  // for all available fields.
  // query the layer with the modified params object

  // layer.queryFeatures(queryParams).then(function(results){
  //   // prints the array of result graphics to the console
  //   console.log('result', results);
  //
  //   if(results.features.length > 0) {
  //     var extent = results.features[0].geometry.getExtent();
  //     results.features.forEach(function(feature) {
  //       extent = extent.union(feature.geometry.getExtent());
  //     })
  //
  //     var zoomTo = extent.expand(1.3);
  //     // zoomTo();
  //     var view = new MapView({
  //       map: map,
  //       container: "viewDiv",
  //       center: [],
  //       zoom: 5
  //     });
  //     view.filter = filter;
  //
  //     view.extent = zoomTo;
  //     view.whenLayerView(layer).then(function(layerView) {
  //       filterLayerView = layerView;
  //       console.log('whenLayerView', layerView);
  //       layerView.filter = {
  //         where: "Country = '${context/country}'"
  //       };
  //       layerView.watch("updating", function(val) {
  //         console.log('updating', val);
  //         // wait for the layer view to finish updating
  //         if (!val) {
  //           view.goTo(zoomTo);
  //           // layerView.queryExtent().then(function(response) {
  //           //   // go to the extent of all the graphics in the layer view
  //           //   console.log('got extent', response.extent);
  //           //   view.goTo(response.extent);
  //           //   // view.goTo(extent);
  //           // });
  //         }
  //       });
  //     });
  //   }
  // });

});
