// inspired by https://github.com/mui-org/material-ui/blob/next/babel.config.js
let defaultPresets = [];
// const env = process.env.LIB_BABEL_ENV || 'umd';
//
// console.log('env', env);

// We release a ES version of the package.
// It's something that matches the latest official supported features of JavaScript.
// Nothing more (stage-1, etc), nothing less (require, etc).
// if (env === 'es') {
//   defaultPresets = [];
// } else {
//   defaultPresets = [
//     [
//       '@babel/preset-env',
//       {
//         targets: { node: 'current' },
//         modules: ['esm', 'umd'].includes(env) ? false : 'commonjs',
//       },
//     ],
//   ];
// }

module.exports = {
  presets: [...defaultPresets,   '@babel/preset-react'],    //
  // customize: require.resolve('babel-preset-react-app/webpack-overrides'),

  plugins: [
    /** mainly required to make storybook work, see
     * - https://github.com/storybooks/storybook/issues/3346#issuecomment-415982589
     * - https://github.com/storybooks/storybook/issues/3346#issuecomment-423719241
     */
    // '@babel/plugin-transform-modules-commonjs',
    // [
    //   '@babel/plugin-transform-runtime',
    //   {
    //     // absoluteRuntime: false,
    //     // corejs: false,
    //     // helpers: true,
    //     regenerator: true,
    //     // version: '7.0.0-beta.0',
    //   },
    // ],
  ],
};

