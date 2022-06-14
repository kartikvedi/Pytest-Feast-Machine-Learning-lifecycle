import time
import re
import pandas as pd

from selenium.webdriver.common.by import By
import pytest

from core.pageobjects import ClustersPageObject
from core.cliobject import CLIObject

def test_login(config, driver):
    pytest.clusters_page = ClustersPageObject(driver, url=config['url'] + '/bdswebui/k8s/clusters')
    pytest.clusters_page.do_login('admin', config['password'])


def test_df_cluster_init(config, driver):
    clusters = config['clusters']
    df_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == True:
            df_cluster = cluster
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
            assert row['Cluster Name'] != df_cluster['name'], 'Cluster already exists'

    #
    # Start creating new one cluster
    #
    btn = driver.find_element(By.ID, 'createK8sClusterBtn')
    btn.click()
    time.sleep(3)


def test_df_cluster_configuration_hosts(config, driver):
    #
    # (1) Host Configuration
    #
    clusters = config['clusters']
    df_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == True:
            df_cluster = cluster
            break
    cluster_name = driver.find_element(By.ID, 'ClusterHostConfigurationForm_label_name')
    cluster_name.send_keys(df_cluster['name'])
    driver.find_element(By.ID, 'ClusterHostConfigurationForm_data_fabric_datafabric').click()

    df_name = driver.find_element(By.ID,'ClusterHostConfigurationForm_data_fabric_datafabric_name')
    df_name.send_keys("df01")

    driver.find_element(By.ID, 'ClusterHostConfigurationForm_data_fabric_three_node_cluster').click()

    #
    # Master nodes
    #
    for hostname in df_cluster["master_nodes_hostnames"]:
        pytest.clusters_page.enable_host(hostname)

    time.sleep(5)

    #
    # Worker nodes
    #
    #for hostname in df_cluster['worker_nodes_hostnames']:
    #    pytest.clusters_page.enable_host(hostname, selector_id=1)
    pytest.clusters_page.click_button('Next')


def test_df_cluster_configuration_kubernetes(config):
    #
    # (2) Cluster Configuration
    #
    clusters = config['clusters']
    df_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == True:
            df_cluster = cluster
            break
    if df_cluster['kubernetes_version'] not in pytest.clusters_page.kubernetes_version:
        pytest.clusters_page.kubernetes_version = df_cluster['kubernetes_version']
    assert df_cluster['kubernetes_version'] in pytest.clusters_page.kubernetes_version

    pytest.clusters_page.click_button('Next')


def test_df_cluster_configuration_auth(config):
    #
    # (3) Authentication
    #
    clusters = config['clusters']
    df_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == True:
            df_cluster = cluster
            break
    if df_cluster['configure_auth']:
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

def test_df_cluster_configuration_apps(config):
    #
    # (4) Application Configuration
    #
    istio = False
    kubeflow = False
    pytest.clusters_page.configure_app(istio, kubeflow)
    pytest.clusters_page.click_button('Next')

    #
    # (5) Summary
    #
    pytest.clusters_page.click_button('Submit')


def test_check_df_cluster_creation(driver, config):
    driver.get(config['url'] + '/bdswebui/k8s/clusters')
    time.sleep(5)
    start_time = time.time()
    creation_time_limit_seconds = config['cluster_creation_max_timeout_seconds']
    clusters = config['clusters']
    df_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == True:
            df_cluster = cluster
            break
    task_done = False

    for i in range(750):
        for table in pytest.clusters_page.get_table():
            for idx, row in table.iterrows():
                if row['Cluster Name'] == df_cluster['name']:
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
        assert start_time + creation_time_limit_seconds > time.time(), 'Datafabric cluster creation time limit exceeded'
    else:
        assert False, 'Unable to finish datafabric creating cluster'



