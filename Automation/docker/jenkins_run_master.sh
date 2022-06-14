#!/bin/sh

if ! [ $ECP_JENKINS_USER ]; then
  echo "ERROR: Please set environment variable 'ECP_JENKINS_USER'"
  exit 1
fi

if ! [ $ECP_JENKINS_TOKEN ]; then
  echo "ERROR: Please set environment variable 'ECP_JENKINS_TOKEN'"
  exit 1
fi

if [ $host_passwd ]; then
  echo "Starting docker..."
  docker run --privileged --net grid \
  --restart always \
  --env host_passwd="$host_passwd" \
  --env LOCAL_DRIVER=False \
  --env ECP_JENKINS_USER=$ECP_JENKINS_USER \
  --env ECP_JENKINS_TOKEN=$ECP_JENKINS_TOKEN \
  --env NO_PROXY="172.17.0.2,172.17.0.1,172.18.0.1" \
  -p 8080:8080 -p 50000:50000 -v /var/jenkins_home:/var/jenkins_home -w /var/jenkins_home \
  jenkins-mlops-master
else
  echo "ERROR: Please set environment variable 'host_passwd'"
fi
