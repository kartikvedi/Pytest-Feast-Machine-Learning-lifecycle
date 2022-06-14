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


def test_nb_examples_init_vars(config, driver):
    #
    # Init test example variables
    #
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    pytest.notebook.replace_line_in_current_cell(f"PASSWORD = '{config['password']}'", 0)
    pytest.notebook.click_save()
    pytest.notebook.click_play()  # Set env: PASSWORD, etc...


def test_nb_examples_kuberefresh(config, driver):
    #
    # KubeRefresh
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output("kubeconfig set for user {0}".format(
        config['login'])), 'Unable to set Kubeflow section variables'

    pytest.notebook.click_play()
    pytest.notebook.click_play()


def test_nb_examples_kubeflow_vars(driver):
    #
    # Go to kubeflow section
    #
    kubeflow_section = driver.find_element(By.ID, 'Kubeflow')
    kubeflow_section.click()
    wait(1)

    #
    # Set kubeflow vars
    #
    pytest.notebook.click_play()  # Pass header
    pytest.notebook.click_play(timeout=5)

    assert pytest.notebook.wait_output(r"env: POD_NAME="), 'Unable to set Kubeflow section variables'


def test_nb_examples_kubeflow_ft_series(driver):
    #
    # FinancialTimeSerieswithFinanceData.ipynb
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'Accuracy\s+=\s+\d+\.\d+'), 'No output from FinancialTimeSerieswithFinanceData.ipynb'


def test_nb_examples_kubeflow_pvctf(driver):
    #
    # pvc-tf-training-fin-series.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r"persistentvolumeclaim/pvctf created|unchanged",
                                       timeout=400), 'Unable to create pvctf'


def test_nb_examples_kubeflow_tfjob(driver):
    #
    # financial-series-tfjob.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r"tfjob.kubeflow.org/trainingjob created|unchanged"), 'Unable to create trainingjob'


def test_nb_examples_kubeflow_training_is_running(driver):
    #
    # while trainingjob-ps-0
    #
    pytest.notebook.click_play()

    assert pytest.notebook.wait_output(r"trainingjob pod is running",
                                       timeout=400), 'Unable to detect trainingjob is running'


def test_nb_examples_kubeflow_tensorflow_serving(driver):
    #
    # logs trainingjob-ps-0
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'Exporting model for tensorflow-serving'), 'Unable to detect tensorflow-serving is running'


def test_nb_examples_kubeflow_finance_sample_created(driver):
    #
    # financial-series-serving.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'inferenceservice.serving.kubeflow.org/finance-sample created|unchanged'), 'Unable to detect finance-sample created'


def test_nb_examples_kubeflow_finance_sample_predictor_is_running(driver):
    """
    """
    #
    # finance-sample-predictor-default-.*-deployment
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'finance-sample-predictor pod is running'), 'Unable to detect finance-sample-predictor pod is running'


def test_nb_examples_kubeflow_kfserving_request(driver):
    #
    # kfserving-request.py
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r"{'predictions': \[{'model-version': '1', 'prediction': 0}]}"), 'Unable to set Kubeflow section variables'


def test_nb_examples_kubeflow_delete_pods(driver):
    #
    # Delete financial-series-serving.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'inferenceservice.serving.kubeflow.org "finance-sample" deleted'), 'Unable delete pod'

    #
    # Delete financial-series-tfjob.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'fjob.kubeflow.org "trainingjob" deleted'), 'Unable to delete pod'

    #
    # Delete pvc-tf-training-fin-series.yaml
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'persistentvolumeclaim "pvctf" deleted', timeout=400), 'Unable to delete pod'


def test_nb_examples_kubeflow_pytorch_create_pvc(driver):
    # Apply pytorch-mnist-ddp-cpu.yaml
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'persistentvolumeclaim/pvcpy created|unchanged'), 'Unable to detect finance-sample-predictor pod is running'


def test_nb_examples_kubeflow_pytorch_create_ddp(driver):
    # pytorch-mnist-ddp-cpu-master-0
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'pytorchjob.kubeflow.org/pytorch-mnist-ddp-cpu created'), 'Unable to detect pytorch-mnist-ddp-cpu is creating'


def test_nb_examples_kubeflow_pytorch_is_running_job(driver):
    # pytorch while
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'pytorch-mnist-ddp-cpu-master-0 pod is running',
        timeout=1800), 'Unable to detect pytorch-mnist-ddp-cpu-master-0 pod is running'


def test_nb_examples_kubeflow_pytorch_logs(driver):
    # pytorch logs
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output('CPU training time=', timeout=1800), 'Unable to logs pod'


def test_nb_examples_kubeflow_pytorch_descr_ddp(driver):
    # Describe  pytorch-mnist-ddp-cpu.yaml
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'Name:\s+pytorch-mnist-ddp-cpu'), 'Unable to describe pod'


def test_nb_examples_kubeflow_pytorch_del_ddp(driver):
    # Delete pytorch-mnist-ddp-cpu.yaml
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(
        r'pytorchjob.kubeflow.org "pytorch-mnist-ddp-cpu" deleted'), 'Unable to delete pod'


def test_nb_examples_kubeflow_pytorch_del_pvc(driver):
    # Delete pvc-pytorch.yaml
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'persistentvolumeclaim "pvcpy" deleted'), 'Unable to delete pod'
