FROM docker.elastic.co/logstash/logstash:5.6.4

## Until an elasticsearch service is available, kill Xpack monitoring
##########################################################################################
ENV XPACK_MONITORING_ENABLED=false

## Get rid of default pipeline and add our own. 
##########################################################################################
RUN rm -f /usr/share/logstash/pipeline/logstash.conf
ADD ./pipeline/ /usr/share/logstash/pipeline/

ADD ./drivers/ /aether/drivers

## Add whatever we need to config. (Nothing for now)
##########################################################################################
# ADD config/ /usr/share/logstash/config/
