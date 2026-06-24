# Frontend (React + Vite) — build estático servido por Nginx.
#
#   docker build -t import-vagas-frontend ./frontend
#
# Etapa 1: compila o SPA. Etapa 2: serve os estáticos e faz proxy reverso de
# /api e /ws para o backend (config em nginx.conf.template).

# ── Etapa 1: build ───────────────────────────────────────────────────────────
FROM node:22-alpine AS build
WORKDIR /app

# Instala dependências primeiro (cache de camada). npm ci usa o package-lock;
# cai para npm install se o lock estiver fora de sincronia.
COPY package.json package-lock.json ./
RUN npm ci || npm install

# Código-fonte e build (tsc -b && vite build → dist/).
COPY . .
RUN npm run build

# ── Etapa 2: runtime ─────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Template processado por envsubst no startup do entrypoint oficial do Nginx.
# Só ${BACKEND_UPSTREAM} é substituído (NGINX_ENVSUBST_FILTER no compose),
# preservando as variáveis nativas do Nginx ($host, $uri, etc.).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Estáticos compilados.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
