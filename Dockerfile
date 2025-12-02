
# ---------- Stage 1: Build React app ----------
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Install dependencies first (for caching)
COPY package*.json ./

RUN npm install --legacy-peer-deps

# Copy rest of the project
COPY . .

# Build the React app
RUN npm run build

# ---------- Stage 2: Serve with Nginx ----------
FROM nginx:stable-alpine

# Copy build output from previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config (optional)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 6005

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
