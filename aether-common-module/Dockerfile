FROM python:3.6

WORKDIR /code

# variable with the requirement file
ARG requirements

COPY ./conf/pip/$requirements /code/conf/pip/requirements.txt

RUN pip install -r /code/conf/pip/requirements.txt

COPY ./ /code

ENTRYPOINT ["/code/entrypoint.sh"]
