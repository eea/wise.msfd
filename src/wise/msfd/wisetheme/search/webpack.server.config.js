const pkg = require('./package.json');

const path = require('path');

const nodeExternals = require('webpack-node-externals');

const BundleAnalyzerPlugin =
  require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

const babelConfig = require('./babel.server.config');

const plugins = [];

if (process.env.BUNDLE_ANALYZE) {
  plugins.push(new BundleAnalyzerPlugin());
}

module.exports = {
  plugins,
  // node: {
  //   react: 'empty'
  // },
  entry: {
    // index: `${__dirname}/src/index.js`,
    server: [`${__dirname}/src/server.js`],
  },
  target: 'node',
  output: {
    // library: pkg.name,
    // libraryTarget: 'commonjs2',
    path: `${__dirname}/dist`,
    filename: '[name].js',
  },
  resolve: {
    extensions: ['.js', '.jsx'],
    alias: {
      // '@eeacms/search': path.resolve('./../searchlib/src'),
    },
    // mainFields: ['main', 'module'], // https://github.com/webpack/webpack/issues/5756#issuecomment-405468106
  },
  devtool: 'source-map',
  mode: 'development',
  module: {
    rules: [
      {
        test: /\.(js|mjs|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: babelConfig,
          },
        ],
      },
    ],
  },
  externals: [nodeExternals()],
};

// "build": "yarn build-csj && yarn build-es && yarn build-esm && yarn build-umd",
// "build-cjs": "BABEL_ENV=production LIB_BABEL_ENV=cjs yarn babel --root-mode upward src --ignore */*.test.js,**/*.test.js,*/*.stories.js,**/stories.js --out-dir dist/cjs",
// "build-esm": "BABEL_ENV=production LIB_BABEL_ENV=esm yarn babel --root-mode upward src --ignore */*.test.js,**/*.test.js,*/*.stories.js,**/stories.js --out-dir dist/esm",
// "build-es": "BABEL_ENV=production LIB_BABEL_ENV=es yarn babel --root-mode upward src --ignore */*.test.js,**/*.test.js,*/*.stories.js,**/stories.js --out-dir dist/es",
// "build-umd": "webpack --mode=production"

