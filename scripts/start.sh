set -ex


./scripts/build_common_and_distribute.sh
./scripts/build_aether_utils_and_distribute.sh

dcpr kernel setup_db
dcpr kernel setup_admin --username 'admin' --password $

docker-compose build
./scripts/create_superusers.py --username oijasdf --password jjjjjjjjjj --services kernel odk ui couchdb-sync

docker-compose build
docker-compose up

