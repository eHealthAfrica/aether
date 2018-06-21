#!/bin/bash
<<<<<<< HEAD
echo "Waiting for kong service to start..."
until $(curl --output /dev/null --silent --head --fail http://kong:8001); do
    sleep 1
done

echo "Starting kongfig push to kong..."
mkdir -p ../kongfig-files
cp -R ./* ../kongfig-files/
cd ../kongfig-files
for file in ./*; do
    echo "Applying ${file##*/}"
    sed -i 's/KONG_CONSUMER/'"${KONG_CONSUMER}"'/g' ./${file##*/}
    sed -i 's/KONG_APIKEY/'"${KONG_APIKEY}"'/g' ./${file##*/}
    sed -i 's/PROJECT_API_URL/'"${PROJECT_API_URL}"'/g' ./${file##*/}
    sed -i 's/KONG_OAUTH2_PROVISION_KEY/'"${KONG_OAUTH2_PROVISION_KEY}"'/g' ./${file##*/}
    kongfig apply --path ./${file##*/} --host kong:8001
=======
echo "Starting kongfig push to kong..."
set -x
for FILE in `ls`; do
    echo "Applying `pwd`/$FILE"
    kongfig apply --path "`pwd`/$FILE" --host kong:8001
>>>>>>> 94a3462e664e7efa79f64c6b94c926bb86d97391
done
