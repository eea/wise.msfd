module.exports = function (grunt) {
  require("load-grunt-tasks")(grunt);

  grunt.loadNpmTasks("grunt-template-html");

  // Config
  var merge = require("merge"),
    config = {};

  config.path = {
    node: "node_modules",
  };

  [require("./grunt/development.js"), require("./grunt/production.js")].forEach(
    function (settings) {
      config = merge.recursive(true, config, settings);
    }
  );

  grunt.initConfig(config);

  // Tasks
  grunt.registerTask("development", [
    "less:development",
    "concat",
    // 'copy'
  ]);

  grunt.registerTask("production", [
    "less:production",
    "concat",
    // 'copy',
    "uglify",
  ]);

  grunt.registerTask("default", ["development", "watch"]);
};
