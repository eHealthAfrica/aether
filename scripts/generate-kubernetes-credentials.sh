gen_pass () {
    openssl rand -base64 16
}

cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: secrets
type: Opaque
stringData:
  
  kernel-admin-password: $(gen_pass)
  kernel-database-user: postgres
  kernel-database-password: $(gen_pass)
  kernel-database-name: aether
  kernel-django-secret-key: $(gen_pass)
  kernel-token: $(gen_pass)
  odk-admin-password: $(gen_pass)
  odk-database-user: postgres
  odk-database-password: $(gen_pass)
  odk-database-name: odk
  odk-django-secret-key: $(gen_pass)
  odk-token: $(gen_pass)
EOF
