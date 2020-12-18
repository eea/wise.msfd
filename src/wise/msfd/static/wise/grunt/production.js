module.exports = {
  less: {
    production: {
      options: {
        compress: true,
        sourceMap: false,
      },
      files: {
        "<%= path.dest %>/css/msfd_search.css": [
          "<%= path.src %>/less/search-form.less",
          "<%= path.src %>/less/select2-override.less",
          "<%= path.src %>/less/select2-top-override.less",
          "<%= path.src %>/less/search-style.less",
        ],
        "<%= path.dest %>/css/tabs.css": [
          "<%= path.src %>/less/tabs.less",
          "<%= path.src %>/less/select2-override.less",
          "<%= path.src %>/less/select2-top-override.less",
        ],
        "<%= path.dest %>/css/compliance.css": [
          "<%= path.src %>/less/compliance.less",
          "<%= path.src %>/less/report-page.less",
          "<%= path.src %>/less/assessment-edit.less",
          "<%= path.src %>/less/translate.less",
          "<%= path.src %>/less/buttons.less",
          "<%= path.src %>/less/bootstrap/tables.less",
          "<%= path.src %>/less/bootstrap/popovers.less",
          "<%= path.src %>/less/bootstrap/tooltips.less",
          "<%= path.src %>/less/bootstrap/modals.less",
          "<%= path.src %>/less/switch.less",
          "<%= path.src %>/less/regional-descriptors.less",
        ],
        "<%= path.dest %>/css/pdf_export.css": [
          "<%= path.src %>/less/pdf_export.less",
        ],
      },
    },
  },
  uglify: {
    scripts: {
      options: {
        sourceMap: {
          includeSources: true,
        },
      },
      files: [
        {
          expand: true,
          cwd: "<%= path.src %>/js",
          src: "**/*.js",
          dest: "<%= path.dest %>/js",
        },
      ],
    },
  },
  postcss: {
    production: {
      src: "<%= path.dest %>/css/*.css",
      options: {
        map: false,
        processors: [require("autoprefixer")()],
      },
    },
  },
  cachebreaker: {
    dev: {
      options: {
        replacement: "md5",
        match: [
          {
            "tabs.css": "dist/css/tabs.css",
            "compliance.css": "dist/css/compliance.css",
            "tabs.js": "dist/js/tabs.js",
            "compliance.js": "dist/js/compliance.js",
            "assessment-edit.js": "dist/js/assessment-edit.js",
            "table-edit.js": "dist/js/table-edit.js",
          },
        ],
      },
      files: {
        src: [
          "../../compliance/pt/css-resources.pt",
          "../../compliance/pt/js-resources.pt",
        ],
      },
    },
  },
};
