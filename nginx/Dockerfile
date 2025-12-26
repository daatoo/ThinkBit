FROM node:20-alpine AS frontend_build
WORKDIR /app

COPY website/package*.json ./website/
WORKDIR /app/website
RUN npm ci

COPY website/ /app/website/

# Set API URL for production build (defaults to /api for nginx proxy)
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginx:alpine
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend_build /app/website/dist /usr/share/nginx/html
