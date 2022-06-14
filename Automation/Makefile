EXTERNAL_ISTIO=false
EXTERNAL_DEX=false
EXTERNAL_SELDON=false

DEX_HELM_RELEASE=dex-mlops-test
ISTIO_DEFAULT=1.12.2

configure-tests:
	./bin/run_test -x -v 	test_configure_authsettings.py \
				test_configure_gateway.py \
				test_configure_hosts.py

install-tests:
	./bin/run_test -x -v 	test_install_platform.py

create-tests:
	./bin/run_test -x -v 	test_create_cluster.py \
				test_create_tenant.py \
				test_create_mlflow.py \
				test_create_training.py \
				test_create_notebook.py

gather-logs-tests:
	./bin/run_test -x -v test_gather_logs.py

kubeflow-tests: install-externals .kubeflow-tests uninstall-externals
.kubeflow-tests:
	./bin/run_test -x -v 	test_kfp.py \
				test_notebook_examples_kf.py \
				test_notebook.py \
				test_sdk_tfjob.py

mlflow-tests:
	./bin/run_test -x -v test_mlflow.py

old-mlflow-tests:
	./bin/run_test -x -v test_old_mlflow.py

s3-tests:
	./bin/run_test -x -v test_s3.py

xgboost-tests:
	./bin/run_test -x -v test_xgboost.py

platform-tests: create-tests configure-tests

install-externals:
	@if [ $(EXTERNAL_ISTIO) = true ] && [ -z "$(shell kubectl get ns | grep istio-system)" ]; then\
	    if [ -z $${ISTIO_VERSION} ]; then \
	        ISTIO_VERSION=$(ISTIO_DEFAULT); \
	    fi;\
	    (cd external ;\
	        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$${ISTIO_VERSION} sh - ;\
	        cd istio-$${ISTIO_VERSION} ;\
	        bin/istioctl install --set profile=demo -y );\
	fi

	@if [ $(EXTERNAL_DEX) = true ]; then\
	    if [ -z $(shell which helm) ]; then\
		./external/get_helm.sh ;\
	    fi ;\
	    helm repo add dex https://charts.dexidp.io > /dev/null ;\
	    helm install $(DEX_HELM_RELEASE) dex/dex ;\
	fi

	@if [ $(EXTERNAL_SELDON) = true ]; then\
	    if [ -z $(shell which helm) ]; then\
		./external/get_helm.sh ;\
	    fi ;\
	    kubectl create namespace seldon-system ;\
	    helm install seldon-core seldon-core-operator \
			--repo https://storage.googleapis.com/seldon-charts \
			--set usageMetrics.enabled=true \
			--namespace seldon-system \
			--set istio.enabled=true \
	    1>/dev/null ;\
	fi

uninstall-externals:
	@if [ $(EXTERNAL_SELDON) = true ]; then\
	    helm uninstall seldon-core --namespace seldon-system ;\
	    kubectl delete namespace seldon-system ;\
	fi

	@if [ $(EXTERNAL_DEX) = true ]; then\
	    helm uninstall $(DEX_HELM_RELEASE) ;\
	fi

	@if [ $(EXTERNAL_ISTIO) = true ]; then\
	    if [ -z $${ISTIO_VERSION} ]; then \
	        ISTIO_VERSION=$(ISTIO_DEFAULT); \
	    fi;\
	    (cd external ;\
		istio-$${ISTIO_VERSION}/bin/istioctl x uninstall --purge -y ;\
		rm -rf istio-$${ISTIO_VERSION} );\
		kubectl delete namespace istio-system;\
	fi

ext-all: ext-istio ext-dex ext-seldon

ext-istio:
	$(eval EXTERNAL_ISTIO=true)
	@echo $(EXTERNAL_ISTIO)

ext-dex:
	$(eval EXTERNAL_DEX=true)
	@echo $(EXTERNAL_DEX)

ext-seldon:
	$(eval EXTERNAL_SELDON=true)
	@echo $(EXTERNAL_SELDON)
