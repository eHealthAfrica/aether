FROM python:3.6

################################################################################
## setup container
################################################################################

COPY conf/docker/* /tmp/
RUN /tmp/setup.sh


################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
RUN pip install -f /code/conf/pip/dependencies -r /code/conf/pip/requirements.txt


COPY package.json /code/package.json
RUN npm install --loglevel silent

ENV PATH /code/node_modules/.bin:$PATH

COPY ./ /code

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false gather2
RUN chown -R gather2: /code

ENTRYPOINT ["/code/entrypoint.sh"]
