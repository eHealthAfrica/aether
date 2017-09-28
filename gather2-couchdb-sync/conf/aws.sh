# Production specific functions

# S3 secrets
configure_aws_cli () {
  mkdir -p ~/.aws
  envsubst < /code/conf/aws_config.tmpl > ~/.aws/config
  export AWS_PROFILE=assume_role
  eval $(aws s3 cp --sse AES256 s3://ecs-secrets-prod/$APP-$PROJECT - )
}

setup_user() {
  # arguments: -u=admin -p=secretsecret -e=admin@gather2.org -t=01234656789abcdefghij
  ./manage.py setup_admin -p=$ADMIN_PASSWORD
}

# run them
configure_aws_cli
setup_user
