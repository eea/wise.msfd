FROM node:14-buster-slim

RUN runDeps="openssl ca-certificates patch git curl" \
 && apt-get update \
 && apt-get install -y --no-install-recommends $runDeps \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN curl -f https://get.pnpm.io/v6.7.js | node - add --global pnpm

RUN mkdir -p /opt/searchproxy \
 && chown -R node /opt/searchproxy

RUN mkdir -p /opt/dependencies \
 && chown -R node /opt/dependencies

WORKDIR /opt/dependencies/

ENV CYPRESS_INSTALL_BINARY=0

RUN git clone https://github.com/eea/searchlib.git \
	&& cd searchlib \
  && git checkout develop \
  && pnpm i

RUN cd /opt/dependencies/searchlib/packages/searchlib \
  && pnpm build

RUN cd /opt/dependencies/searchlib/packages/searchlib-less \
  && pnpm build

RUN cd /opt/dependencies/searchlib/packages/searchlib-middleware \
  && pnpm build

COPY . /opt/searchproxy/

WORKDIR /opt/searchproxy/

RUN cd /opt/searchproxy \
	&& pnpm link ../dependencies/searchlib/packages/searchlib \
  && pnpm link ../dependencies/searchlib/packages/searchlib-less \
  && pnpm link ../dependencies/searchlib/packages/searchlib-middleware

RUN cd /opt/searchproxy \
  && pnpm i

RUN cd /opt/searchproxy \
  && pnpm build:server

CMD pnpm run server

EXPOSE 7000
