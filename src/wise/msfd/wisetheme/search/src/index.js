import React from 'react';
import ReactDOM from 'react-dom';
import { SearchApp, registry } from '@eeacms/search';
import installConfig from './config';

import '@elastic/react-search-ui-views/lib/styles/styles.css';
import '@eeacms/search-less/dist/main.css';

import './less/custom.less';

// ++resource++measures-catalogue/
// import './index.css';

const configRegistry = installConfig(registry);
console.log('cofnig', configRegistry);

ReactDOM.render(
  <SearchApp registry={configRegistry} appName="wise" />,
  document.getElementById('search-app'),
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// import reportWebVitals from './reportWebVitals';
// reportWebVitals();
