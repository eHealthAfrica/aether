ls -la $HOME/.cache/pip
whoami
id
id -g
DC_TEST="docker-compose -f docker-compose-travis-test.yml"
$DC_TEST build "$1"-test
$DC_TEST run "$1"-test test_travis 