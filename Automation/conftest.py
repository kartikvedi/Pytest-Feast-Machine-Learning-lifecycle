import os
import time
import datetime
import json
import logging
import pytest
from pydoc import locate

from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from core.cliobject import CLIObject, UserMachine

logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)
LOCAL_DRIVER = False if 'LOCAL_DRIVER' in os.environ and os.environ['LOCAL_DRIVER'] == 'False' else True
HOST_PASSWD = os.environ['host_passwd'] if 'host_passwd' in os.environ else None
ECP_JENKINS_USER = os.environ['ECP_JENKINS_USER'] if 'ECP_JENKINS_USER' in os.environ else None
ECP_JENKINS_TOKEN = os.environ['ECP_JENKINS_TOKEN'] if 'ECP_JENKINS_TOKEN' in os.environ else None


def pytest_addoption(parser):
    print(r'''
─────▄█████▄─────
───▄█▌▒▐█████▄───
──███▒▒████████──
─███▌▒▐█████████─
████▒▒▒▒▀██▒▒▒▒▀█
███▌▒██▒▐█▌▒██▒▐█
███▒▐█▌▒██▒▐█▌▒██
██▌▒██▒▐█▌▒██▒▐██
██▒▐█▌▒██ ▒▒▒▒███
─███████▌▒██████─
──██████▒▐█████──
───▀███▌▒█yTest──
─────▀█████▀─────
''')

    parser.addoption("--config", action="store", default="platform.json",
                     help="Config file or json data. Syntax: --config=file:filename.txt")
    parser.addoption("--override_config", action="append", help="Override values in config file", default=None)
    parser.addoption("--host_passwd", action="store", help="Root password for hosts", default=HOST_PASSWD)
    parser.addoption("--ecp_jenkins_user", action="store", help="User for trigger remote jobs",
                     default=ECP_JENKINS_USER)
    parser.addoption("--ecp_jenkins_token", action="store", help="Password for trigger remote jobs",
                     default=ECP_JENKINS_TOKEN)


@pytest.fixture
def config(request):
    """
    Parse input string with different data formats:
        - json:{json: data}
        - file:filename
    :param request: input string of data
    :return: JSON dictionary
    """
    params = request.config.getoption("--config")
    override_params = request.config.getoption("--override_config")

    data_content = params
    data_format = 'file'

    if len(params) > 4 and params[4:5] == ':':
        data_content = params[5:]
        data_format = params[:5]

    if data_format == 'json:':
        data = json.loads(params[5:])
    else:  # Default data format is 'file'
        with open(data_content) as json_file:
            data = json.load(json_file)

    # overriding values in data from '--override_config' argument
    if override_params is not None:
        for override_param in override_params:
            parsed_data = override_param.split("=", 1)
            if len(parsed_data) != 2:
                _log.warning(
                    f"Override parameter `{override_param}` is invalid, expected value like `cluster.name=c1`, skipping")
                continue
            param_key = parsed_data[0]
            param_val = parsed_data[1]

            # TODO: handle dots and colons in the name of the key
            key_path = param_key.split(".")
            cur_obj = data
            for i, cur_path in enumerate(key_path):
                if i == len(key_path) - 1:
                    parse_type = cur_path.split(":", 1)
                    if len(parse_type) == 2:
                        cur_path = parse_type[0]
                        parse_type = locate(parse_type[1])
                    else:
                        parse_type = None

                    if cur_path in cur_obj and parse_type is None:
                        parse_type = type(cur_obj[cur_path])

                    if parse_type is not None:
                        try:
                            cur_obj[cur_path] = parse_type(param_val)
                            _log.info(f"Parameter {override_param} has been applied with type `{parse_type}`")
                        except Exception as e:
                            _log.warning(
                                f"Cannot cast override parameter `{override_param}` with value `{param_val}` "
                                f"to type `{parse_type}`, skipping")
                            _log.warning(e)
                            continue
                    else:
                        cur_obj[cur_path] = param_val
                        _log.info(f"Parameter {override_param} has been applied with type `str`")
                else:
                    if cur_path not in cur_obj:
                        cur_obj[cur_path] = {}
                    cur_obj = cur_obj[cur_path]

    return data


@pytest.fixture
def host_passwd(request):
    return request.config.getoption("--host_passwd")


@pytest.fixture
def ecp_jenkins_user(request):
    return request.config.getoption("--ecp_jenkins_user")


@pytest.fixture
def ecp_jenkins_token(request):
    return request.config.getoption("--ecp_jenkins_token")

@pytest.fixture
def exec_cmd_with_output_handler(config, host_passwd):
    cluster = config['clusters'][0]
    master_node_machine = UserMachine(ip_address=cluster['master_nodes'][0], password=host_passwd)
    
    def _exec_cmd_with_output(cmd: str, match_string: str = None):
        return CLIObject().exec_cmd_with_output_from_obj(master_node_machine, cmd, match_string)
    
    return _exec_cmd_with_output

@pytest.fixture
def exec_cmd_handler(config, host_passwd):
    cluster = config['clusters'][0]
    master_node_machine = UserMachine(ip_address=cluster['master_nodes'][0], password=host_passwd)
    
    def _exec_cmd(cmd: str):
        return CLIObject().exec_cmd_from_obj(master_node_machine, cmd)
    
    return _exec_cmd

@pytest.fixture(scope='module')
def driver(request):
    PROXY = "172.17.0.1:3128"
    prox = Proxy()
    prox.proxy_type = ProxyType.MANUAL
    prox.http_proxy = PROXY
    prox.https_proxy = PROXY
    prox.ssl_proxy = PROXY
    options = webdriver.ChromeOptions()
    options.set_capability('acceptInsecureCerts', True)
    # options.set_capability('proxy', prox)
    if LOCAL_DRIVER:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Remote(
            command_executor='http://172.18.0.1:4444/wd/hub',
            options=options
        )
    # request.addfinalizer(driver.quit)
    return driver


def pytest_configure():
    pytest.notebook = None
    pytest.platform = None


# set up a hook to be able to check if a test has failed
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


# check if a test has failed
@pytest.fixture(scope="function", autouse=True)
def test_failed_check(request):
    yield
    # request.node is an "item" because we use the default
    # "function" scope
    if request.node.rep_setup.failed:
        _log.warning(f"setting up a test failed! -> {request.node.nodeid}")
    elif request.node.rep_setup.passed:
        if request.node.rep_call.failed and 'driver' in request.node.funcargs:
            driver = request.node.funcargs['driver']
            take_screenshot(driver, request.node.nodeid)
            _log.warning(f"executing test failed -> {request.node.nodeid}")


# make a screenshot with a name of the test, date and time
def take_screenshot(driver, nodeid):
    images_dir = 'images'
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    time.sleep(1)
    file_name = f'{nodeid}_{datetime.datetime.today().strftime("%Y-%m-%d_%H:%M")}.png'.replace("/", "_").replace("::",
                                                                                                                 "__")
    driver.save_screenshot(os.path.join(images_dir, file_name))
