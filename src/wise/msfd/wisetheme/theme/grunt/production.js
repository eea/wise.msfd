module.exports = {
  less: {
    production: {
      options: {
        compress: true,
        sourceMap: false,
      },
      files: {
        "static/css/theme-compiled.css": "less/theme.local.less",
        "static/css/critical.css": "less/critical.less",
      },
    },
  },

  postcss: {
    options: {
      map: true,
      processors: [
        require("autoprefixer")({
          browsers: ["last 2 versions"],
        }),
      ],
    },
    dist: {
      src: "less/*.css",
    },
  },

  concat: {
    scripts: {
      files: {
        "static/js/theme-compiled.js": ["js/**/*.js"],
      },
    },
  },

  uglify: {
    scripts: {
      files: {
        "static/js/theme-compiled.js": ["static/js/theme-compiled.js"],
      },
    },
  },
};
