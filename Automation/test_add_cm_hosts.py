import time
import logging
import pytest

from core.pageobjects import HostsPageObject

_log = logging.getLogger(__name__)


def test_hosts_login(config, driver):
    pytest.hosts_page = HostsPageObject(driver, url=config['url'] + '/bdswebui/k8s/hosts')
    pytest.hosts_page.do_login('admin', config['password'])

@pytest.mark.skip
def test_cm_hosts_configure(config, driver, host_passwd):
    hosts_conf = config['hosts']
    clusters = config['clusters']
    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break

    cm_hosts_list = cm_cluster['master_nodes'] + cm_cluster['worker_nodes']
    cm_hosts = ",".join(cm_hosts_list)

    driver.get(config['url'] + '/bdswebui/k8s/hosts')
    time.sleep(5)

    _log.info(f"Configure Compute Host IP range: {cm_hosts}")

    pytest.hosts_page.submit_form(ip_list=cm_hosts, password=host_passwd, datafabric=False)
    time.sleep(6)

    #
    # Here we expect at least one host will be found with status 'running bundle'.
    # But possible host configured manually and status already changed to 'phase 1 of 2 completed', it would be FAIL,
    # we shouldn't touch other sessions.
    #
    list_hosts_bundle = pytest.hosts_page.select_hosts(with_status='running bundle', click=False)
    list_hosts_phase1 = pytest.hosts_page.select_hosts(cm_hosts_list, with_status='phase 1 of 2 completed')
    expected_count = len(list_hosts_phase1) + len(list_hosts_bundle)
    _log.info(f'Boundle hosts: {list_hosts_bundle}')
    _log.info(f'Phase1 hosts: {list_hosts_phase1}')
    count = 0
    if expected_count > 0:
        count = pytest.hosts_page.wait_rows_status_by_column(column='Status', value='phase 1 of 2 completed',
                                                             timeout=hosts_conf['hosts_creation_max_timeout_seconds'],
                                                             count_limit=expected_count)
    assert count == expected_count, 'Phase 1 hosts preparation error'


def test_cm_hosts_install(config, driver):
    hosts_conf = config['hosts']
    clusters = config['clusters']
    driver.get(config['url'] + '/bdswebui/k8s/hosts')
    time.sleep(10)

    cm_cluster = {}
    for cluster in clusters:
        if "datafabric" in cluster and cluster["datafabric"] == False:
            cm_cluster = cluster
            break

    cm_hosts_list = cm_cluster['master_nodes'] + cm_cluster['worker_nodes']


    #
    # Snapshot current hosts state
    #
    list_hosts_phase1 = pytest.hosts_page.select_hosts(cm_hosts_list, with_status='phase 1 of 2 completed')
    list_hosts_ready = pytest.hosts_page.select_hosts(cm_hosts_list, with_status='ready', click=False)
    count_expected_ready = len(list_hosts_phase1) + len(list_hosts_ready)

    _log.info(f'Phase1 hosts: {list_hosts_phase1}')
    _log.info(f'Ready hosts: {list_hosts_ready}')
    #
    # Do installation
    #
    if len(list_hosts_phase1) > 0:
        pytest.hosts_page.install_hosts()

    #
    # Wait and check hosts statuses
    #
    count = 0
    if count_expected_ready > 0:
        count = pytest.hosts_page.wait_rows_status_by_column(column='Status', value='ready',
                                                             timeout=hosts_conf['hosts_creation_max_timeout_seconds'],
                                                             count_limit=count_expected_ready)

    #
    # Final verdict
    #
    assert count == count_expected_ready, 'Not all hosts configured successfully'
