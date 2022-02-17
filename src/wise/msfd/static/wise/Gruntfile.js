module.exports = function (grunt) {
  require('load-grunt-tasks')(grunt);

  grunt.loadNpmTasks('grunt-cache-breaker');

  // Config
  var merge = require('merge'),
    config = {};

  config.path = {
    static: '.',
    src: 'src',
    node: 'node_modules',
    dest: 'dist',
  };

  [
    // require("./grunt/base.js"),
    require('./grunt/development.js'),
    require('./grunt/production.js'),
  ].forEach(function (settings) {
    config = merge.recursive(true, config, settings);
  });

  grunt.initConfig(config);

  // Tasks
  grunt.registerTask('development', ['less:development', 'copy']);

  grunt.registerTask('production', [
    'less:production',
    'copy',
    'uglify',
    'postcss',
    'cachebreaker',
  ]);

  grunt.registerTask('default', ['development', 'watch']);
};
