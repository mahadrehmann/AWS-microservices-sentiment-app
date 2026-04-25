# =============================================================================
# Microservice B — Frontend Dockerfile
# =============================================================================
# Based on nginx:alpine (tiny ~23 MB base image).
# Copies static files and our custom nginx.conf.
# No build step needed — pure static HTML/CSS/JS.
# =============================================================================

FROM nginx:1.25-alpine

# Remove the default Nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy static frontend files
COPY index.html  /usr/share/nginx/html/index.html
COPY style.css   /usr/share/nginx/html/style.css
COPY app.js      /usr/share/nginx/html/app.js

# Replace default Nginx config with our custom one
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Nginx runs as PID 1 in the foreground
CMD ["nginx", "-g", "daemon off;"]
