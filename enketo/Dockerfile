FROM node

WORKDIR /code

# COPY package.json /code/package.json

# RUN git clone https://github.com/enketo/enketo-core.git
# RUN ls /code/enketo-core

COPY ./ /code

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
# RUN useradd -ms /bin/false aether
# RUN chown -R aether: /code

# ENTRYPOINT ["/code/entrypoint.sh"]

WORKDIR /code/

WORKDIR /code/enketo-transformer
#

RUN npm install
RUN ls node_modules
# RUN npm install

# ENV PATH /code/enketo-transformer/node_modules/.bin:$PATH

ENTRYPOINT ["/code/entrypoint.sh"]
