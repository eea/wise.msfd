module.exports = {
  less: {
    development: {
      options: {
        compress: false,
        sourceMap: true,
        sourceMapFilename: '<%= path.dest %>/css/source.css.map',
        sourceMapURL: './source.css.map'
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
            '<%= path.src %>/less/report-page.less',
            '<%= path.src %>/less/assessment-edit.less',
            '<%= path.src %>/less/translate.less',
            '<%= path.src %>/less/switch.less',
            '<%= path.src %>/less/regional-descriptors.less',
          ]
      }
    }
  },
  copy: {
    scripts: {
      files: [
        { expand: true,
          flatten: true,
          src: [
            '<%= path.src %>/js/*.js'
          ],
          dest: '<%= path.dest %>/js/'
        }
      ]
    }
  },
  watch: {
    styles: {
      files: ['<%= path.src %>/less/**/*.less'],
      tasks: ['less:development'],
      options: {
        nospawn: true
      }
    },
    scripts: {
      files: ['<%= path.src %>/js/**/*.js'],
      tasks: ['copy'],
      options: {
        nospawn: true
      }
    },
    templates: {
      files: ['<%= path.static %>/src/tpl/**/*.hbs'],
      tasks: ['template:dev'],
      options: {
        nospawn: true
      }
    }
  }
};
