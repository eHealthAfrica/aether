FROM python:3.6

################################################################################
## setup container
################################################################################

COPY ./conf/docker/* /tmp/
RUN /tmp/setup.sh


################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
RUN pip install -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt

COPY ./ /code

################################################################################
## copy application version and create git revision 
################################################################################
ARG VERSION
RUN echo $VERSION > VERSION
ARG GIT_REVISION
RUN echo $GIT_REVISION > REVISION 

################################################################################
## Config kong apis using kongfig 
################################################################################
COPY ./kongfig.yml /kongfig.yml
ARG KONG_CONSUMER
ARG KONG_APIKEY
ARG PROJECT_API_URL
ARG KONG_OAUTH2_PROVISION_KEY
RUN sed -i 's/KONG_CONSUMER/'"$KONG_CONSUMER"'/g' /kongfig.yml
RUN sed -i 's/KONG_APIKEY/'"$KONG_APIKEY"'/g' /kongfig.yml
RUN sed -i 's/PROJECT_API_URL/'"$PROJECT_API_URL"'/g' /kongfig.yml
RUN sed -i 's/KONG_OAUTH2_PROVISION_KEY/'"$KONG_OAUTH2_PROVISION_KEY"'/g' /kongfig.yml
RUN npm install kongfig -g --loglevel error

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
