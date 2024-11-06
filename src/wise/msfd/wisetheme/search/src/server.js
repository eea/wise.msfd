import runtime from 'regenerator-runtime/runtime'; // compatibility with react-speech-recognition

import { registry } from '@eeacms/search';
import { makeServer } from '@eeacms/search-middleware';
import installConfig from './config';

console.log('runtime', runtime);
const configRegistry = installConfig(registry);

const app = makeServer(configRegistry.searchui.wise);
const port = process.env.PORT || '7000';

app.listen(port, () => {
  console.log(`ES Proxy app running on http://localhost:${port}`);
});
