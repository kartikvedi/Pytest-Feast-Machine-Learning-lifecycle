import time
import re
import pandas as pd

from selenium.webdriver.common.by import By
import pytest

from core.pageobjects import ClustersPageObject


def test_login(config, driver):
    pytest.clusters_page = ClustersPageObject(driver, url=config['url'] + '/bdswebui/k8s/clusters')
    pytest.clusters_page.do_login('admin', config['password'])


def test_cm_cluster_init(config, driver):
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break

    #
    # Open clusters page
    #
    time.sleep(2)
    el = driver.find_element(By.XPATH, '//*[@id="bdsApp"]/div/main/div/div/div[1]/h1')
    assert el.text == 'Kubernetes Cluster'

    #
    # Check cluster already exists
    #
    for table in pytest.clusters_page.get_table():
        for idx, row in table.iterrows():
            assert row['Cluster Name'] != cm_cluster['name'], 'Cluster already exists'

    #
    # Start creating new one cluster
    #
    btn = driver.find_element(By.ID, 'createK8sClusterBtn')
    btn.click()
    time.sleep(3)


def test_cm_cluster_configuration_hosts(config, driver):
    #
    # (1) Host Configuration
    #
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    cluster_name = driver.find_element(By.ID, 'ClusterHostConfigurationForm_label_name')
    cluster_name.send_keys(cm_cluster['name'])
    time.sleep(5)

    #
    # Master nodes
    #
    for hostname in cm_cluster['master_nodes_hostnames']:
        pytest.clusters_page.enable_host(hostname)
    time.sleep(2)

    #
    # Worker nodes
    #
    for hostname in cm_cluster['worker_nodes_hostnames']:
        pytest.clusters_page.enable_host(hostname, selector_id=1)
    time.sleep(2)
    pytest.clusters_page.click_button('Next')


def test_cm_cluster_configuration_kubernetes(config):
    #
    # (2) Cluster Configuration
    #
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    if cm_cluster['kubernetes_version'] not in pytest.clusters_page.kubernetes_version:
        pytest.clusters_page.kubernetes_version = cm_cluster['kubernetes_version']
    assert cm_cluster['kubernetes_version'] in pytest.clusters_page.kubernetes_version

    pytest.clusters_page.click_button('Next')


def test_cm_cluster_configuration_auth(config):
    #
    # (3) Authentication
    #
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    if cm_cluster['configure_auth']:
        auth = config['auth']
        pytest.clusters_page.configure_auth(
            security=auth['security'],
            auth_type=auth['auth_type'],
            service_host=auth['service_host'],
            service_port=auth['service_port'],
            user_attribute=auth['user_attribute'],
            base_dn=auth['base_dn'],
            bind_dn=auth['bind_dn'],
            bind_pwd=auth['bind_pwd']
        )
    pytest.clusters_page.click_button('Next')


def test_cm_cluster_configuration_apps(config):
    #
    # (4) Application Configuration
    #
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    istio = True if cm_cluster['apps']['istio'] else False
    kubeflow = True if cm_cluster['apps']['kubeflow'] else False
    pytest.clusters_page.configure_app(istio, kubeflow)
    pytest.clusters_page.click_button('Next')

    #
    # (5) Summary
    #
    pytest.clusters_page.click_button('Submit')


def test_cm_check_cluster_creation(driver, config):
    driver.get(config['url'] + '/bdswebui/k8s/clusters')
    time.sleep(5)
    start_time = time.time()
    clusters = config['clusters']
    creation_time_limit_seconds = config['cluster_creation_max_timeout_seconds']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    task_done = False

    for i in range(750):
        for table in pytest.clusters_page.get_table():
            for idx, row in table.iterrows():
                if row['Cluster Name'] == cm_cluster['name']:
                    st = row['Status']
                    if st == 'creating':
                        time.sleep(5)
                    if st == 'ready':
                        task_done = True
                    if st == 'deleting':
                        # !!!Warning, cluster will be deleted!!!
                        pass
                    break
            else:
                assert False, 'No rows with created cluster found!'
        if task_done:
            break
        assert start_time + creation_time_limit_seconds > time.time(), 'Cluster creation time limit exceeded'
    else:
        assert False, 'Unable to finish creating cluster'


def test_configure_proxy_on_master_node(exec_cmd_with_output_handler, config):
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break
    kubeflow = True if cm_cluster['apps']['kubeflow'] else False
    expected_output = 'deployment.apps/controller env updated'
    if kubeflow:
        assert exec_cmd_with_output_handler('kubectl set env deployment/controller -n knative-serving http_proxy=$http_proxy',
                                            expected_output)[0] is True, 'Unable to apply http proxy'
        assert exec_cmd_with_output_handler('kubectl set env deployment/controller -n knative-serving https_proxy=$https_proxy',
                                            expected_output)[0] is True, 'Unable to apply https proxy'
        assert exec_cmd_with_output_handler('kubectl set env deployment/controller -n knative-serving no_proxy=$no_proxy',
                                            expected_output)[0] is True, 'Unable to apply no proxy'
    else:
        pytest.skip("Kubeflow addon is disabled")
