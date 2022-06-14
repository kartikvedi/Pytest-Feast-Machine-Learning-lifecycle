import time
import socket

from core.pageobjects import NotebookPageObject, EzmeralPlatform
from selenium.webdriver.common.by import By
import logging
import pytest

logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)

def wait(value):
    time.sleep(float(value))

def test_ldap_is_alive(config):
    auth = config['auth']
    remote_server = (auth['service_host'], int(auth['service_port']))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_result = client_socket.connect_ex(remote_server)
    assert connect_result == 0, 'LDAP server is down'


def test_nb_login(config, driver):
    notebook = config['notebook']

    if 'url' not in notebook:
        _log.info('Logging in to Platform')
        platform = EzmeralPlatform(driver, url=config['url'] + '/bdswebui/k8stenant/notebooks/#kubedirector')
        platform.do_login(config['login'], config['password'])
        notebook_url = platform.get_app_url(notebook['name'])
    else:
        notebook_url = notebook['url']

    assert notebook_url is not None, 'Unable to determine notebook URL endpoint!'
    pytest.notebook = NotebookPageObject(driver, url=notebook_url,
                                         max_response_timeout=config['notebook']['command_execution_max_timeout'])
    _log.info('Logging in to Notebook')
    assert pytest.notebook.do_login(config['login'], config['password']), 'Unable to logging in to the Notebook'
    assert 'JupyterLab' in driver.title

def test_close_all_kernels(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()

def test_open_prerequisite(config, driver):
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/prerequite.ipynb')

def test_execute_prerequisite(config, driver):
    #
    # Init test example variables
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output("kubeconfig set for user {0}".format(
        config['login'])), 'Unable to set Kubeflow section variables'
    pytest.notebook.click_play()  # Set env: PASSWORD, etc...
    assert pytest.notebook.wait_output("Kubeflow client set"), 'Unable to set Kubeflow section variables'

def test_open_kale(config, driver):
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/kale.ipynb')

def test_enable_kale_deployement_panel(config, driver):
    time.sleep(2)
    el= driver.find_element(By.XPATH, "//li[@id='tab-key-6']/div")
    el.click()
    time.sleep(2)
    el = driver.find_element(By.XPATH, "//input[@name='enableKale']")
    el.click()
    time.sleep(2)
    el = driver.find_element(By.XPATH, "//input[@name='enableKale']")
    el.click()
    time.sleep(2)
    el = driver.find_element(By.XPATH,"//div[@id='kubeflow-kale/kubeflowDeployment']/div/div[2]/div[2]/div/div/div/button/span")
    el.click()
