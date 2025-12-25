FROM node:20-alpine AS frontend_build
WORKDIR /app

COPY website/package*.json ./website/
WORKDIR /app/website
RUN npm ci

COPY website/ /app/website/
RUN npm run build

FROM nginx:alpine
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend_build /app/website/dist /usr/share/nginx/html
