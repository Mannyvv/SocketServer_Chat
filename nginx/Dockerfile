FROM nginx:1.21-alpine
# Deletes the default.conf file that comes when you install nginx.
RUN rm /etc/nginx/conf.d/default.conf

# Copies our custom nginx.conf file into the same folder that the default.conf file
# was in, replacing it.
COPY nginx.conf /etc/nginx/conf.d

# Create a directory for SSL certificates within the NGINX container
RUN mkdir -p /etc/nginx/ssl/

# Copy SSL certificate and key to the NGINX container
# COPY cert.pem /etc/nginx/ssl/
# COPY mykey.key /etc/nginx/ssl

LABEL maintainer="Manny"
LABEL org.label-schema.name="nginx container"
LABEL org.label-schema.vcs-ref="nginx container"
 