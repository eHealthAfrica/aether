DCA="docker-compose -f ./docker-compose-auth.yml"

$DCA kill
$DCA down
$DCA up -d kongpg
sleep 3
$DCA run kong kong migrations up
$DCA up -d --build kong kongpg keycloak keycloakpg
$DCA build auth
$DCA run auth setup_auth
$DCA run auth make_realm
$DCA kill auth
$DCA up -d auth
