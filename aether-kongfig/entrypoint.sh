#!/bin/bash
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
done
