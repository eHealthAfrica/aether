FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
ADD conf/aether_couchdb_sync.conf /etc/nginx/conf.d/default.conf
