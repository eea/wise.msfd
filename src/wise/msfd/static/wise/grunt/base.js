module.exports = {
 template: {
    dev: {
      engine: 'handlebars',
      cwd: 'src/tpl/',
      partials: ['src/tpl/partials/*.hbs'],
      // data: 'test/fixtures/data/data.json',
      options: {
      },
      files: [
        {
          expand: true,     // Enable dynamic expansion.
          cwd: 'src/tpl/',      // Src matches are relative to this path.
          src: '*.hbs', // Actual pattern(s) to match.
          dest: './',   // Destination path prefix.
          ext: '.html'  // Dest filepaths will have this extension.
        }
      ]
    }
  }
};
