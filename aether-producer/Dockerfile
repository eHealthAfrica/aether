FROM python:3.7-slim-stretch as bigimage

################################################################################
## setup container
################################################################################

RUN apt-get update -qq && \
    apt-get -qq \
        --yes \
        --allow-downgrades \
        --allow-remove-essential \
        --allow-change-held-packages \
        install gcc

RUN apt-get --yes install python3-dev
RUN apt-get --yes install git
RUN apt-get --yes install build-essential
RUN apt-get --yes install make

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf/pip /code/conf/pip
# COPY ./conf/pip/.pydistutils.cfg /root/.pydistutils.cfg

RUN pip install -q --upgrade pip 
# RUN apt-get install --yes librdkafka-dev
RUN git clone https://github.com/edenhill/librdkafka.git ./librdkafka
WORKDIR /code/librdkafka
RUN ./configure --install-deps && make && make install
# RUN git clone https://github.com/confluentinc/confluent-kafka-python.git /code/confluent-kafka 
# WORKDIR /code/confluent-kafka

ENV LD_LIBRARY_PATH=/usr/local/lib


RUN pip install --global-option=build_ext --global-option="-I/usr/local/include/" --global-option="-L/usr/local/lib" --global-option="-g" --no-clean --no-binary :all: confluent-kafka



# RUN pip install --global-option=build_ext --global-option="-I/usr/local/include/" --global-option="-L/usr/local/lib" --global-option="-g" --no-clean  .
# RUN python setup.py build_ext --inplace
# RUN pip wheel --wheel-dir=/root/wheels .

# # NEW BUILD
# FROM python:3.7-slim-stretch

# RUN apt-get update -qq && \
#     apt-get -qq \
#         --yes \
#         --allow-downgrades \
#         --allow-remove-essential \
#         --allow-change-held-packages \
#         install gcc

# COPY --from=bigimage /root/wheels /root/wheels
# COPY --from=bigimage /usr/local/lib/ /usr/local/lib
# COPY --from=bigimage /usr/local/include/librdkafka /usr/local/include/librdkafka


# RUN pip install --no-binary :all: confluent-kafka


# RUN pip install \
#       --find-links=/root/wheels \
#       --no-binary :all: confluent-kafka

COPY ./conf/pip /code/conf/pip

RUN pip install -r /code/conf/pip/requirements.txt

COPY ./ /code

WORKDIR /code

################################################################################
## copy application version and create git revision
################################################################################

ARG VERSION
ARG GIT_REVISION

RUN mkdir -p /var/tmp && \
    echo $VERSION > /var/tmp/VERSION && \
    echo $GIT_REVISION > /var/tmp/REVISION

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["/code/entrypoint.sh"]
