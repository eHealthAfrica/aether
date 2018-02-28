#!/bin/bash	
set -e	
	
# Production specific functions	
	
check_variable() {	
  if [ -n "$1" ];	
  then	
    echo "$2 in Ordnung!"	
  else	
    echo "Missing $2"	
    exit -1	
  fi	
}	
	
check_kernel() {	
  # check if KERNEL env variables were set	
  check_variable $AETHER_KERNEL_URL   "KERNEL url"	
  check_variable $AETHER_KERNEL_TOKEN "KERNEL token"	
}	
	
check_odk() {	
  if [[ "$AETHER_MODULES" == *odk* ]];	
  then	
    # check if ODK env variables were set only if it's included in the modules list.	
    check_variable $AETHER_ODK_URL   "ODK url"	
    check_variable $AETHER_ODK_TOKEN "ODK token"	
  fi	
}	
	
check_kernel	
check_odk	
check_variable $ADMIN_PASSWORD "ADMIN password"	
