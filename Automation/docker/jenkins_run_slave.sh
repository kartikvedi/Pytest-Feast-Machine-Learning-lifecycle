#!/bin/sh

master_url="http://mip-bd-ap07-n4-vm05.mip.storage.hpecorp.net:8080"
#secret="f33951f6f87f8f8f7f76f6f7f7f8f7f6f87f87f8f7f876f876f876f87ff876c7"
#agent_name="SeleniumVM2"

if ! [ $secret ]; then
  echo "ERROR: Please set environment variable 'secret', goto jenkins master: $master_url"
  exit 1
fi

if ! [ $agent_name ]; then
  echo "ERROR: Please set environment variable 'agent_name'"
  exit 1
fi

if [ $host_passwd ]; then
  echo "Starting docker..."
  export no_proxy=$no_proxy,mip-ap78-n2-vm05.mip.storage.hpecorp.net,16.0.12.236,16.0.8.118
  docker run -v /var/jenkins_home:/var/jenkins_home \
  --restart always \
  --env host_passwd="$host_passwd" \
  --env LOCAL_DRIVER=False \
  --env NO_PROXY="172.17.0.2,172.17.0.1,172.18.0.2" \
  --init jenkins-mlops-slave \
  -url $master_url \
  -workDir=/var/jenkins_home \
  $secret $agent_name
else
  echo "ERROR: Please set environment variable 'host_passwd'"
fi
