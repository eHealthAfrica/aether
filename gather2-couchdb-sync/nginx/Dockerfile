FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
# this is overridden for local dev in docker-compose.yml
ADD conf/gather2_couchdb_sync.conf /etc/nginx/conf.d/default.conf
