import time
import socket
import datetime
from core.pageobjects import NotebookPageObject, EzmeralPlatform
from selenium.webdriver.common.by import By
import logging
import pytest

logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)

def wait(value):
    time.sleep(float(value))

def check_text_exist(output, text):
    if text in output:
        return True
    else:
        return False

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

@pytest.mark.skip
def test_nb_open_install_package(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/MLFlow/Bike-Sharing-Usecase/InstallPackage.ipynb')


def test_nb_restart_kernel(driver):
    #
    # Restart kernel
    #
    _log.info('Restart kernel')
    pytest.notebook.click_restart_kernel()
    time.sleep(2)

def test_nb_execute_install_package(config,driver):
    pytest.notebook.click_all_play()

    # for i in pytest.notebook.get_output_arr():
    #     _log.info(i.text)
    # output = (pytest.notebook.get_output_arr()[-2]).text
    endTime = datetime.datetime.now() + datetime.timedelta(minutes=30)
    status = False
    while True:
        elements = driver.find_elements(By.CLASS_NAME,
                                        "lm-Widget p-Widget jp-InputPrompt jp-InputArea-prompt".replace(' ', '.'))
        elements = [element.text for element in elements]
        if "[*]:" in elements:
            _log.info("Waiting for all cells to be executed.")
            time.sleep(20)
        else:
            status = True
            break
        if datetime.datetime.now() >= endTime:
            status = False
            break
    assert status, "Execution of Notebook not finished in 30 minutes."
    outputs = pytest.notebook.get_output_arr()
    outputs = [output.text for output in outputs if output.text != '']
    assert check_text_exist(outputs[-1], 'Successfully installed pydotplus-2.0.2'), 'Pydotplus package is not installed'

def test_nb_open_BikeSharing(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/MLFlow/Bike-Sharing-Usecase/Bike-Sharing-MLFlow.ipynb')


def test_nb_execute_all_bikesharing_usecase(config,driver):
    pytest.notebook.click_all_play()
    endTime = datetime.datetime.now() + datetime.timedelta(minutes=30)
    status = False
    while True:
        elements = driver.find_elements(By.CLASS_NAME,
                                        "lm-Widget p-Widget jp-InputPrompt jp-InputArea-prompt".replace(' ', '.'))
        elements = [element.text for element in elements]
        if "[*]:" in elements:
            _log.info("Waiting for all cells to be executed.")
            time.sleep(20)
        else:
            status = True
            break
        if datetime.datetime.now() >= endTime:
            status = False
            break
    assert status, "Execution of Notebook not finished in 30 minutes."
    outputs = pytest.notebook.get_output_arr()
    outputs = [output.text for output in outputs if output.text != '']
    assert check_text_exist(outputs[-1], 'Running'), 'Error - Failed to exceute bikesharing'

@pytest.mark.skip
def test_nb_open_prediction(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/MLFlow/Bike-Sharing-Usecase/Prediction.ipynb')

@pytest.mark.skip
def test_nb_execute_prediction(config,driver):
    pytest.notebook.click_all_play()
    endTime = datetime.datetime.now() + datetime.timedelta(minutes=30)
    status = False
    while True:
        elements = driver.find_elements(By.CLASS_NAME,
                                        "lm-Widget p-Widget jp-InputPrompt jp-InputArea-prompt".replace(' ', '.'))
        elements = [element.text for element in elements]
        if "[*]:" in elements:
            _log.info("Waiting for all cells to be executed.")
            time.sleep(20)
        else:
            status = True
            break
        if datetime.datetime.now() >= endTime:
            status = False
            break
    assert status, "Execution of Notebook not finished in 30 minutes."
    outputs = pytest.notebook.get_output_arr()
    outputs = [output.text for output in outputs if output.text != '']
    # for i in pytest.notebook.get_output_arr():
    #     _log.info(i.text)
    # output = (pytest.notebook.get_output_arr()[-2]).text
    assert check_text_exist(outputs[-1], 'Prediction Passed.'), 'Error - Failed to exceute prediction.ipynb'