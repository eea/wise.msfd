descr_values = {
  "D1":"Biodiversity",
  "D2":"NIS",
  "D3":"Commercial fish",
  "D4":"Food webs",
  "D5":"Eutrophication",
  "D6":"Sea floor integrity",
  "D7":"Hydrographical alteration",
  "D8":"Contaminants",
  "D9":"Contaminants in seafood",
  "D10":"Marine litter",
  "D11":"Introduction of energy"
}

function rename_key(doc, old_key, new_key){
  if (old_key !== new_key) {
    doc[new_key] = doc[old_key];
    delete doc[old_key];
  }
  return doc;
}

function normalize_doc(doc){
  let keys = Object.keys(doc)
  for (var i = 1; i < keys.length; i++){
    let old_key = keys[i];
    let new_key = old_key.replace(/[\W_]+?/g,"_");
    doc = rename_key(doc, old_key, new_key)
  }
  return doc;
}

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

module.exports = function(doc){
    const _ = require('underscore');
    let modified_doc = {}
    modified_doc = _.extend(modified_doc, doc);

//console.log(modified_doc)

    try{
      var descriptors = [];
      var descriptors_flags = [];
      for (var i = 1; i < 12; i++){
        if (modified_doc['D' + i] !== 0){
          descriptors.push(descr_values['D' + i]);
          descriptors_flags.push('D' + i);
        }
      }
      modified_doc['Descriptors'] = descriptors;
      modified_doc['Descriptors_flags'] = descriptors_flags;

      if (modified_doc['Sector'] === 'Ports and Traffic'){
        modified_doc['Sector'] = 'Ports and traffic';
      }

      if (modified_doc['Use or activity'] === 'not specified'){
        modified_doc['Use or activity'] = 'Not specified';
      }

      if ((modified_doc['Status'] === 'not specified') || (modified_doc['Status'] === '')){
        modified_doc['Status'] = 'Not specified';
      }

      if (modified_doc['Status'] === 'ident'){
        modified_doc['Status'] = 'Identified';
      }

      if (modified_doc['Status'] === 'taken'){
        modified_doc['Status'] = 'Taken';
      }

      if (modified_doc['Status'] === 'notident'){
        modified_doc['Status'] = 'Not identified';
      }

      if (modified_doc['Spatial scope'] === 'not specified'){
        modified_doc['Spatial scope'] = 'Not specified';
      }

      if (modified_doc['Measure impacts to'] === 'Nos specified'){
        modified_doc['Measure impacts to'] = 'Not specified';
      }

      let notm = modified_doc['Nature of the measure'].split(", ");
      let notm_list = [];
      for (var i = 0; i < notm.length; i++){
        if (notm[i] === "technical measure"){
          notm[i] = "technical measures"
        }
        notm_list.push(notm[i].capitalize());
      }
      modified_doc['Nature of the measure'] = notm_list;
      modified_doc = normalize_doc(modified_doc);
    }
    catch(err){
        console.log(err);
        console.log("Index the document without modifications");
        modified_doc = doc;
    }
    return modified_doc;
}
