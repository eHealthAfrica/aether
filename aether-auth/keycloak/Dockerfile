# This is required to run Keycloak behind KONG @ /keycloak/
# We just edit the default standalone configs from the base image.

FROM jboss/keycloak:latest
USER jboss
RUN sed -i -e 's/<web-context>auth<\/web-context>/<web-context>keycloak\/auth<\/web-context>/' /opt/jboss/keycloak/standalone/configuration/standalone.xml
RUN sed -i -e 's/<web-context>auth<\/web-context>/<web-context>keycloak\/auth<\/web-context>/' /opt/jboss/keycloak/standalone/configuration/standalone-ha.xml