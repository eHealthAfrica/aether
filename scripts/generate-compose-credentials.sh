gen_pass () {
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
}

cat << EOF
COUCHDB_USER=admin
COUCHDB_PASSWORD=$(gen_pass)

AETHER_KERNEL_TOKEN=$(gen_pass)
AETHER_ODK_TOKEN=$(gen_pass)

KERNEL_ADMIN_USERNAME=admin
KERNEL_ADMIN_PASSWORD=$(gen_pass)
KERNEL_DJANGO_SECRET_KEY=$(gen_pass)
KERNEL_RDS_PASSWORD=$(gen_pass)

ODK_ADMIN_PASSWORD=$(gen_pass)
ODK_DJANGO_SECRET_KEY=$(gen_pass)
ODK_RDS_PASSWORD=$(gen_pass)

COUCHDB_SYNC_ADMIN_PASSWORD=$(gen_pass)
COUCHDB_SYNC_DJANGO_SECRET_KEY=$(gen_pass)
COUCHDB_SYNC_RDS_PASSWORD=$(gen_pass)
COUCHDB_SYNC_REDIS_PASSWORD=$(gen_pass)
COUCHDB_SYNC_GOOGLE_CLIENT_ID=

UI_ADMIN_PASSWORD=$(gen_pass)
UI_DJANGO_SECRET_KEY=$(gen_pass)
UI_RDS_PASSWORD=$(gen_pass)
EOF
