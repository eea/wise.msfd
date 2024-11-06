module.exports = {
  less: {
    development: {
      options: {
        paths: [],
        strictMath: false,
        sourceMap: true,
        outputSourceFiles: true,
        sourceMapFileInline: true,
        sourceMapURL: "++theme++wise-theme/less/theme-compiled.less.map",
        sourceMapFilename: "less/theme-compiled.less.map",
        modifyVars: {
          isPlone: "false",
        },
      },
      files: {
        "static/css/theme-compiled.css": "less/theme.local.less",
        "static/css/critical.css": "less/critical.less",
      },
    },
  },

  // copy: {
  //   scripts: {
  //       files: [
  //           { expand: true,
  //               flatten: true,
  //               src: [
  //                   'js/*.js'
  //               ],
  //               dest: 'static/js/'
  //           }
  //       ]
  //   }
  // },

  concat: {
    scripts: {
      files: {
        "static/js/theme-compiled.js": ["js/**/*.js"],
      },
    },
  },

  watch: {
    styles: {
      files: ["less/*.less", "barceloneta/less/*.less", "custom/less/*.less"],
      tasks: ["less:development"],
      options: {
        nospawn: true,
      },
    },
    scripts: {
      files: ["js/**/*.js"],
      tasks: ["concat"],
      // tasks: ['copy'],
      options: {
        nospawn: true,
      },
    },
  },
};
