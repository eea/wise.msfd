## Wise Catalog of Measures


This application  uses the EEA Semantic Search library.

To test it, run:

```
git clone https://github.com/eea/searchlib
cd searchlib
pnpm m build
```

Then, inside this folder:

```
pnpm link ../path/to/searchlib/packages/searchlib
pnpm link ../path/to/searchlib/packages/searchlib-less
pnpm build
```

Then create a new folder, set the layout to [@@measures-search](http://localhost:8080/Plone/@@measures-search)

There are 3 different modes to run the app:

- `pnpm run start` runs a live development server, outside of Plone. Use [localhost:3000](http://localhost:3000) for quickest development path.

- `pnpm run watch` builds the index.html and resources to develop and use the page in Plone
- `pnpm run build` static builds the index.html and resources for final use in Plone


### Running the ElasticSearch Proxy

The ElasticSearch proxy is run with the `src/server.js` Node app. It is
a simple frontend over the `@eeacms/search-middleware` that connects with the
local configuration. To run it, you need to configure the `PROXY_ES_DSN`
environment variable:

```
env PROXY_ES_DSN=http://localhost:9200/_all node src/server.js
```

There is a Dockerfile to build this as a separate app.
