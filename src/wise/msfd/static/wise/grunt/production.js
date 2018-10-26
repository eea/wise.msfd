module.exports = {
  less: {
    production: {
      options: {
        compress: true,
        sourceMap: false
      },
      files: {
        '<%= path.dest %>/css/msfd_search.css': [
          '<%= path.src %>/less/search-form.less',
          '<%= path.src %>/less/select2-override.less',
          '<%= path.src %>/less/select2-top-override.less',
          '<%= path.src %>/less/search-style.less'
        ],
        '<%= path.dest %>/css/tabs.css' : [
          '<%= path.src %>/less/tabs.less',
          '<%= path.src %>/less/select2-override.less',
          '<%= path.src %>/less/select2-top-override.less'
        ],
        '<%= path.dest %>/css/compliance.css': [
          '<%= path.src %>/less/compliance.less',
          '<%= path.src %>/less/translate.less',
        ]
      }
    }
  },
  uglify: {
    scripts: {
      options: {
        sourceMap : {
          includeSources: true
        }
      },
      files: [{
        expand: true,
        cwd: '<%= path.src %>/js',
        src: '**/*.js',
        dest: '<%= path.dest %>/js'
      }]
    }
  },
  postcss: {
    production: {
      src: '<%= path.dest %>/css/*.css',
      options: {
        map: false,
        processors: [
          require('autoprefixer')()
        ]
      }
    }
  }
};
