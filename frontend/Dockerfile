# Stage 1: Build Vite React Application
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json ./

# Clean dependency installation
RUN npm ci

# Copy full application code and build
COPY . .
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine

# Copy built static files from build stage to Nginx web root
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration for client-side routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]