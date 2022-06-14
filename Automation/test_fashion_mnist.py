import time
import logging
import pytest
import socket
import datetime
from selenium.webdriver.common.by import By
from core.platform_prepare import add_secrets
from core.pageobjects import TenantPageObject, AddUserPageObject,NotebookPageObject,EzmeralPlatform

logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)

@pytest.mark.skip()
def test_pvc_creation(config, exec_cmd_with_output_handler):
    tenant = "kubeflow"
    yaml = f"""kubectl apply -n {tenant} -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: fashion-mnist-pvc
spec:
    accessModes:
    - ReadWriteMany
    resources:
        requests:
            storage: 2Gi
EOF"""

    res = exec_cmd_with_output_handler(cmd=yaml, match_string='persistentvolumeclaim/fashion-mnist-pvc created')[0]
    assert res, "Failed to create PVC"

@pytest.mark.skip()
def test_download_data_files(config, exec_cmd_with_output_handler):
    files = [
        'https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/t10k-images-idx3-ubyte.gz',
        'https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/t10k-labels-idx1-ubyte.gz',
        'https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/train-images-idx3-ubyte.gz',
        'https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/train-labels-idx1-ubyte.gz'
    ]

    command = '''wget -q {} ; if [ $? -eq 0 ]; then echo "D" ; else echo "F"; fi'''
    assert exec_cmd_with_output_handler(command.format(files[0]), "D")[0],"Failed to Download File"
    assert exec_cmd_with_output_handler(command.format(files[1]), "D")[0],"Failed to Download File"
    assert exec_cmd_with_output_handler(command.format(files[2]), "D")[0],"Failed to Download File"
    assert exec_cmd_with_output_handler(command.format(files[3]), "D")[0],"Failed to Download File"

@pytest.mark.skip()
def test_create_pod(config, exec_cmd_with_output_handler):
    tenant = "kubeflow"
    yaml = f"""kubectl apply -n {tenant} -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
    name: dataaccess
spec:
    containers:
    - name: alpine
      image: alpine:latest
      command: ['sleep', 'infinity']
      volumeMounts:
      - name: mypvc
        mountPath: /data
    volumes:
    - name: mypvc
      persistentVolumeClaim:
        claimName: fashion-mnist-pvc
EOF"""

    res = exec_cmd_with_output_handler(cmd=yaml, match_string='pod/dataaccess created')[0]
    assert res, "Failed to create Pod"

@pytest.mark.skip()
def test_copy_files_pod(config,exec_cmd_with_output_handler):
    time.sleep(60)
    tenant = "kubeflow"
    files = [
        "t10k-images-idx3-ubyte.gz",
        "t10k-labels-idx1-ubyte.gz",
        "train-images-idx3-ubyte.gz",
        "train-images-idx3-ubyte.gz",
    ]

    command = "kubectl cp {} dataaccess:/data -n {}"
    exec_cmd_with_output_handler(command.format(files[0],tenant), "File {} Copied.".format(files[0]))
    exec_cmd_with_output_handler(command.format(files[1],tenant), "File {} Copied.".format(files[1]))
    exec_cmd_with_output_handler(command.format(files[2],tenant), "File {} Copied.".format(files[2]))
    exec_cmd_with_output_handler(command.format(files[2],tenant), "File {}Copied.".format(files[3]))

@pytest.mark.skip()
def test_delete_pod(config,exec_cmd_with_output_handler):
    tenant = "kubeflow"
    command = f"kubectl delete pod dataaccess -n {tenant}"
    assert exec_cmd_with_output_handler(command,'''pod "dataaccess" deleted''')[0],"Failed to delete pod dataccess pod"


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


def test_close_all_kernels(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()


def test_open_notebook(config, driver):
    _log.info('Close kernel sessions')
    pytest.notebook.close_kernel_sessions()
    _log.info('Open example')
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/HPECP5.4/Fashion-MNIST-Keras-GPU-Pipeline/Fashion-MNIST-GPU-KF-Pipeline.ipynb')


def test_execute_notebook(config,driver):
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
    assert check_text_exist(outputs[-1], 'Running'), 'Error - Failed to exceute notebook'

@pytest.mark.skip()
def test_check_status_pipeline(config,exec_cmd_with_output_handler):
    pass
