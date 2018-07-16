FROM python:3.6-jessie

WORKDIR /code

COPY ./conf/pip/requirements.txt /code/conf/pip/requirements.txt

RUN pip install -r /code/conf/pip/requirements.txt

COPY ./ /code

ENTRYPOINT ["/code/entrypoint.sh"]
