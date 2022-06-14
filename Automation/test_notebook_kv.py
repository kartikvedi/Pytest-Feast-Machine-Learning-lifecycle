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


def test_cleanup_notebook(config, exec_cmd_with_output_handler):
    notebook = config['notebook']['name']
    homedir = '/opt/guestconfig/appconfig'
    ns = config["tenant"]["name"] if 'tenant' in config else 'dev1'
    yaml_list = ['examples/kubeflow/financial-series/serving/financial-series-serving.yaml',
                 'examples/kubeflow/financial-series/training/financial-series-tfjob.yaml',
                 'examples/kubeflow/financial-series/training/pvc-tf-training-fin-series.yaml',
                 'examples/kubeflow/pytorch-training/pytorch-mnist-ddp-cpu.yaml',
                 'examples/kubeflow/pytorch-training/pvc-pytorch.yaml'
                 ]
    pod_cmd = f'''kubectl get pods -n {ns} -o custom-columns=NAME:.metadata.name|grep {notebook}-controller-'''
    _, pod = exec_cmd_with_output_handler(pod_cmd)
    pod = pod.strip()
    for yaml in yaml_list:
        cmd = f'kubectl -n {ns} exec {pod} -- kubectl delete -f {homedir}/{yaml} -n {ns}'
        _log.info(cmd)
        exec_cmd_with_output_handler(cmd)


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


def test_nb_open_example(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/HPE.ipynb')


def test_nb_restart_kernel(driver):
    #
    # Restart kernel
    #
    _log.info('Restart kernel')
    pytest.notebook.click_restart_kernel()
    time.sleep(1)
    pytest.notebook.confirm_dialog()
    time.sleep(1)

@pytest.mark.skip
def test_nb_examples_init_vars(config, driver):
    #
    # Init test example variables
    pytest.notebook.replace_line_in_current_cell(f"PASSWORD = '{config['password']}'", 0)
    pytest.notebook.click_save()
    pytest.notebook.click_play()  # Set env: PASSWORD, etc...

@pytest.mark.skip
def test_nb_examples_kuberefresh(config, driver):
    #
    # KubeRefresh
    #
    pytest.notebook.replace_line_in_current_cell(f"%kubeRefresh --pwd $PASSWORD ", 0)
    pytest.notebook.click_save()
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output("kubeconfig set for user {0}".format(
        config['login'])), 'Unable to set Kubeflow section variables'

def test_nb_examples_executeAll(config,driver):
    pytest.notebook.click_all_play()
    output = (pytest.notebook.get_output_arr()[-1]).text
    assert pytest.notebook.wait_output("kubeconfig set for user {0}".format(
        config['login'])), 'Unable to set Kubeflow section variables'





































