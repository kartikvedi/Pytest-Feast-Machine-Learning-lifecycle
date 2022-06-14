SELENIUM_HUB_HOST=16.0.8.118
SELENIUM_VM2_HOST=16.0.8.119

all:
	@echo =====================================================
	@echo Usage commands:
	@echo
	@echo jenkins_create_master - Prepare jenkins master docker image
	@echo jenkins_create_slave  - Prepare jenkins slave docker image
	@echo jenkins_run_master    - Start docker with jenkins master instance
	@echo jenkins_run_slave     - Start docker with jenkins slave instance
	@echo selenium_create_grid_hub    - Create and start selenium grid hub with client
	@echo selenium_create_grid_client - Create and start selenium client
	@echo =====================================================

#
# Selenium docker
#

selenium_create_grid_hub:
	docker network create grid
	docker run -d --net grid -p 4442-4444:4442-4444 --name selenium-hub selenium/hub:4.1.2-20220208
	docker run -d --net grid -e SE_EVENT_BUS_HOST=$(SELENIUM_HUB_HOST) \
--shm-size="2g" \
-e SE_EVENT_BUS_PUBLISH_PORT=4442 \
-e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
selenium/node-chrome:4.1.2-20220208

selenium_create_grid_client:
	docker network create grid
	docker run -d -p 5556:5556 \
--shm-size="2g" \
-e SE_EVENT_BUS_HOST=$(SELENIUM_HUB_HOST) \
-e SE_EVENT_BUS_PUBLISH_PORT=4442 \
-e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
-e SE_NODE_HOST=$(SELENIUM_VM2_HOST) \
-e SE_NODE_PORT=5556 \
selenium/node-chrome:4.1.2-20220208

#
# Jenkins docker
#

jenkins_create_master:
	cp -f ../requirements.txt .
	docker build . -f Dockerfile-jenkins-master -t jenkins-mlops-master
	rm -f requirements.txt

jenkins_create_slave:
	cp -f ../requirements.txt .
	docker build . -f Dockerfile-jenkins-slave -t jenkins-mlops-slave
	rm -f requirements.txt

jenkins_run_master:
	./jenkins_run_master.sh

jenkins_run_slave:
	./jenkins_run_slave.sh

#
# System Docker
#

install_docker:
	sudo yum install docker-ce docker-ce-cli containerd.io
	sudo systemctl start docker
	@echo Don\'t forget to add jenkins user to docker group
	sudo mkdir -p /var/jenkins_home
	sudo chown jenkins /var/jenkins_home
