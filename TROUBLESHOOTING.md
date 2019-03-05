# TROUBLESHOOTING

This is the list of most common problems and how to solve them.

## Docker issues

Visit:
- [docker command line reference](https://docs.docker.com/engine/reference/commandline/cli/)
- [docker-compose command line reference](https://docs.docker.com/compose/reference/overview/)

Sometimes helps.


### Run out of space

Docker loves memory, building a container creates a bunch of cached images that
will remain forever in the system till you remove them.

How to free space:

```bash
# remove running generated containers:
#   aether_kernel_1,
#   aether_kernel_2,
#   ...,
#   aether_kernel_n
./scripts/clean_all.sh
# based on
# https://docs.docker.com/compose/reference/down/
docker-compose down

# remove unused data
# https://docs.docker.com/engine/reference/commandline/system_prune/
docker system prune --all --volumes --force

# remove ALL (clean start after it):
#   intermediate containers,
#   built containers,
#   pulled images,
#   volumes
#   ...
# https://docs.docker.com/compose/reference/down/
docker-compose down --rmi all -v
```


### [UBUNTU] `ERROR: Couldn't connect to Docker daemon at http+docker://localunixsocket - is it running?`

This happens because you don't have enough permissions to access the container
volumes. Sometimes the directories belong to the `root` user instead of your user.

Check the folders with `ls -l`

```text
$ ls -l aether-client-library/

total 96
drwxr-xr-x  4  root    root     aether
drwxr-xr-x  4  my-user my-user  conf
drwxr-xr-x  2  root    root     dist
-rw-r--r--  1  my-user my-user  docker-compose.yml
-rw-r--r--  1  my-user my-user  Dockerfile
-rwxr-xr-x  1  my-user my-user  entrypoint.sh
-rw-r--r--  1  my-user my-user  MANIFEST.in
-rw-r--r--  1  my-user my-user  README.md
-rw-r--r--  1  my-user my-user  setup.cfg
-rw-r--r--  1  my-user my-user  setup.py
```

To set you as directories owner:

```bash
sudo chown $USER: * -R
```
Check again

```text
$ ls -l aether-client-library/

total 96
drwxr-xr-x  4  my-user my-user  aether
drwxr-xr-x  4  my-user my-user  conf
drwxr-xr-x  2  my-user my-user  dist
-rw-r--r--  1  my-user my-user  docker-compose.yml
-rw-r--r--  1  my-user my-user  Dockerfile
-rwxr-xr-x  1  my-user my-user  entrypoint.sh
-rw-r--r--  1  my-user my-user  MANIFEST.in
-rw-r--r--  1  my-user my-user  README.md
-rw-r--r--  1  my-user my-user  setup.cfg
-rw-r--r--  1  my-user my-user  setup.py
```
