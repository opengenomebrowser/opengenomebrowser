#!/bin/bash

# To avoid running uwsgi as root, create new user, then run start.sh as this user.
#
# Reason: OpenGenomeBrowser writes files to the folder structure. If uwsgi is root,
#   all files will belong to root.

re='^[0-9]+$'
if ! [[ $USER_ID =~ $re ]]; then
  echo "Error: Environment variable USER_ID is ill-defined!" >&2
  exit 1
fi
if ! [[ $GROUP_ID =~ $re ]]; then
  echo "Error: Environment variable GROUP_ID is ill-defined!" >&2
  exit 1
fi

if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "false" ]; then
  echo "DEBUG is $DEBUG"
else
  echo "Error: Environment variable DEBUG is ill-defined!" >&2
  exit 1
fi

if id user &>/dev/null; then
  echo 'USER ALREADY EXISTS'
else
  echo 'CREATE USER'

  # create new user in container
  addgroup --gid $GROUP_ID user
  adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user

  # give user ownership of relevant locations inside container
  sudo chown -R user:user /root
  sudo chown -R user:user /tmp
  sudo chown -R user:user /opt

  # in production mode give user ownership of code and socker
  if [ "$DEBUG" = "false" ]; then
    sudo chown -R user:user /socket
    sudo chown -R user:user /opengenomebrowser
  fi

  # add user to sudoers
  echo '%sudo ALL=(ALL) NOPASSWD:ALL' >>/etc/sudoers
fi

# generate secret key if none exists
if [ -z ${DJANGO_SECRET_KEY+x} ]; then
  echo "GENERATE DJANGO_SECRET_KEY"
  export DJANGO_SECRET_KEY="$(date | sha256sum | base64 | head -c 60)"
fi

# start django
sudo -u user --preserve-env bash -c "cd '$PWD'; ./start.sh"
