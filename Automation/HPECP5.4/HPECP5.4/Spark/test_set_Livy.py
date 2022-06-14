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


def test_nb_open_setLivy(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/Spark/Wind-Turbine-Power-Prediction-PySpark-Livy-DataTap/setLivy.ipynb')


def test_nb_restart_kernel(driver):
    #
    # Restart kernel
    #
    _log.info('Restart kernel')
    pytest.notebook.click_restart_kernel()
    time.sleep(1)
    pytest.notebook.confirm_dialog()
    time.sleep(1)

def test_nb_setLivy(config, driver):
    #
    # Init test example variables
    #
    pytest.notebook.replace_line_in_current_cell(f"%setLivy --url {config['livy']['url']} --pwd {config['password']}", 0)
    pytest.notebook.click_save()
    pytest.notebook.click_play()  # Set env: PASSWORD, etc...

def test_nb_restart_kernel(driver):
    #
    # Restart kernel
    #
    _log.info('Restart kernel')
    pytest.notebook.click_restart_kernel()
    time.sleep(1)
    pytest.notebook.confirm_dialog()
    time.sleep(1)

def test_nb_open_WindTurbine(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/Spark/Wind-Turbine-Power-Prediction-PySpark-Livy-DataTap/WindTurbinePowerPrediction.ipynb')

def test_nb_WindTurbine_executeAll(config,driver):
    pytest.notebook.click_all_play()
    output = (pytest.notebook.get_output_arr()[-1]).text
    flag = False
    files = ['dtap://TenantStorage/Scada-Model/GBM.model/treesMetadata','dtap://TenantStorage/Scada-Model/GBM.model/metadata','dtap://TenantStorage/Scada-Model/GBM.model/data']
    for file in files:
        if file in output:
            flag = True
        else:
            flag =  False
            break
    assert flag, "not able to list model files"