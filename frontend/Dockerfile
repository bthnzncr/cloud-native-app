# Build stage
FROM node:23-alpine AS build-stage

WORKDIR /app

# Accept the VITE_API_URL argument
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy app source and build with the environment variable
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine AS production-stage

# Copy built files to nginx public directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
