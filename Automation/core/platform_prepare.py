import os
import datetime
import time
import re
import logging
import json

import requests
import jenkins
from ping3 import ping
from urllib import request
from core.cliobject import CLIObject

_log = logging.getLogger(__name__)
_cli = CLIObject()
is_300GB_disk = True


class JenkinsAPI:
    def __init__(self, jenkins_url='https://ez-jenkins.mip.storage.hpecorp.net:8443', jenkins_user=None,
                 jenkins_token=None):
        self._jenkins_user = jenkins_user
        self._jenkins_token = jenkins_token
        self._jenkins_url = jenkins_url
        self._server = jenkins.Jenkins(jenkins_url, username=jenkins_user, password=jenkins_token)
        self.headers = {'Content-Type': 'application/json'}

    def get_jenkins_crumb(self):
        res = requests.get(f"{self._jenkins_url}/crumbIssuer/api/json",
                           verify=False,
                           headers=self.headers,
                           auth=(self._jenkins_user, self._jenkins_token))
        data = res.json()
        return data['crumbRequestField'], data['crumb']

    def jenkins_os_install(self, list_nodes):
        crumb_field = self.get_jenkins_crumb()
        res = requests.post(f"{self._jenkins_url}/job/OS_install/buildWithParameters",
                            verify=False,
                            data={"host_public_IPs": " ".join(list_nodes),
                                  "add_os_blocking_file": "no",
                                  "check_os_blocking_file": "no",
                                  "worker_node": "MIPworker2"
                                  },
                            headers={crumb_field[0]: crumb_field[1]},
                            auth=(self._jenkins_user, self._jenkins_token)
                            )
        logging.info(res.text)
        if res.status_code == 201:
            return True
        else:
            return False

    def jenkins_ecp_build_and_deploy(self, list_nodes):
        crumb_field = self.get_jenkins_crumb()
        res = requests.post(f"{self._jenkins_url}/job/ECP_build_and_deploy/buildWithParameters",
                            data={"host_public_IPs": " ".join(list_nodes),
                                  "add_os_blocking_file": "no",
                                  "check_os_blocking_file": "no",
                                  "addons": "istio kubeflow"
                                  },
                            verify=True,
                            headers={crumb_field[0]: crumb_field[1]},
                            auth=(self._jenkins_user, self._jenkins_token)
                            )
        if res.status_code == 201:
            return True
        else:
            return False

    def jenkins_get_os_build_by_id(self, build_id=None):
        crumb_field = self.get_jenkins_crumb()
        self.headers[crumb_field[0]] = crumb_field[1]
        print(self.headers)
        if build_id is None:
            build_id = "lastBuild"
        res = requests.get(f"{self._jenkins_url}/job/OS_install/api/json",
                           headers=self.headers,
                           verify=False,
                           auth=(self._jenkins_user, self._jenkins_token)
                           )
        data = res.json()
        logging.info(res.status_code)
        if build_id == "lastBuild":
            return data['id']
        else:
            return data['result']

    def build_info(self, build_id):
        res = self._server.get_build_info('OS_install', build_id)['result']
        return res


def ip_range_to_list(ip_range):
    """
    Extend short IP list range into full list of ip's.
    :param ip_range: text str at least one full ip address should be specified
    :return: list
    """
    network = re.search(r'(\d+\.\d+\.\d+)\.', ip_range)
    base_net = network.group(1)
    ip_range = ip_range.replace(base_net, '').replace('.', '')
    ranges = (x.split("-") for x in ip_range.split(","))
    return [f'{base_net}.{i}' for r in ranges for i in range(int(r[0]), int(r[-1]) + 1)]


def wait_jenkins_job(jenkins_srv, build_id):
    res = None
    deadline = datetime.datetime.now() + datetime.timedelta(minutes=35)
    while datetime.datetime.now() < deadline:
        res = jenkins_srv.build_info(build_id)
        if res is not None:
            break
        time.sleep(30)

    if res == "SUCCESS":
        return True

    _log.error("Jenkins JOB is not successful")
    return False


def os_install(ip_list, jenkins_url=None, jenkins_user=None, jenkins_token=None):
    jenkins_srv = JenkinsAPI(jenkins_url, jenkins_user, jenkins_token)

    for _ in range(10):
        try:
            if jenkins_srv.jenkins_os_install(ip_list):
                break
        except json.RequestsJSONDecodeError:
            _log.warning('Something wrong with remote Jenkins or Network, sleep for 20 seconds...')
            time.sleep(20)
    else:
        _log.error("error with jenkins_os_install")
        return False

    build_id = int(jenkins_srv.jenkins_get_os_build_by_id())

    _log.info("waiting job")
    res = wait_jenkins_job(jenkins_srv, build_id)

    return res


def uninstall_platform(controller_machine):
    """
    Uninstall platform from controller and find successful message in output logs
    :param controller_machine: UserMachine, store all needed data for creating ssh connections
    :return: True/False
    """
    _log.info('uninstall platform')
    return _cli.exec_cmd_with_output_from_obj(controller_machine, "./hpe_platform.bin  -a erase",
                                              'BlueData software was successfully erased from the server')[0]


def download_and_install_platform_bin(controller_machine, bin_url, platform_password):
    bin_name = "hpe_platform.bin"

    _cli.exec_cmd_with_output_from_obj(controller_machine, "yum install wget -y")
    # _cli.exec_cmd_with_output_from_obj(controller_machine, f'wget --progress=dot:mega -c "{bin_url}" -O {bin_name}')
    _cli.exec_cmd_with_output_from_obj(controller_machine, f"chmod +x {bin_name}")

    install_cmd = f"./{bin_name} --default-password {platform_password} --action install --prechecks-config-file /tmp/hpecp_prechecks --skipeula"

    res, _ = _cli.exec_cmd_with_output_from_obj(controller_machine, install_cmd, 'Successfully installed HPE CP')

    if not res and is_300GB_disk:
        _cli.exec_cmd_with_output_from_obj(controller_machine, install_cmd)
        cmd_hack = "sed -i -e 's/\\x27MIN_PERSISTENT_DISK_SIZE_GB\\x27 : 500/\\x27MIN_PERSISTENT_DISK_SIZE_GB\\x27 : 150/g' /usr/share/bdswebui/bdswebui/settings.py"
        _cli.exec_cmd_with_output_from_obj(controller_machine, cmd_hack)
        _cli.exec_cmd_from_obj(controller_machine, "reboot > /dev/null 2>&1 &")
        time.sleep(20)
        reboot_deadline = datetime.datetime.now() + datetime.timedelta(minutes=5)
        while datetime.datetime.now() < reboot_deadline:
            if ping(controller_machine.ip):
                _log.info('Ping OK')
                res = True
                time.sleep(5)
                break
            time.sleep(10)
        else:
            _log.error("node failed to start after reboot")
            return False

    return res


def add_secrets(exec_cmd_with_output_handler, tenant):
    tpl_s3 = f'''kubectl apply -n {tenant} -f - <<EOF
apiVersion: v1
data:
  S3_ACCESS_KEY_ID: YWRtaW4K
  S3_SECRET_ACCESS_KEY: YWRtaW4xMjMK
kind: Secret
metadata:
  name: s3-cred
  labels:
    kubedirector.hpe.com/secretType: mlflow-s3-credentials
type: Opaque
EOF
'''
    tpl_mlflow = f'''
kubectl apply -n {tenant} -f - <<EOF
apiVersion: v1
data:
  MLFLOW_ARTIFACT_ROOT: czM6Ly9tbGZsb3c= #s3://mlflow
  AWS_ACCESS_KEY_ID: YWRtaW4= #admin
  AWS_SECRET_ACCESS_KEY: YWRtaW4xMjM= #admin123
kind: Secret
metadata:
  name: mlflow-sc
  labels:
    kubedirector.hpe.com/secretType: mlflow
type: Opaque
EOF
'''
    res = True
    res &= exec_cmd_with_output_handler(cmd=tpl_s3, match_string='secret/s3-cred created')[0]
    res &= exec_cmd_with_output_handler(cmd=tpl_mlflow, match_string='secret/mlflow-sc created')[0]

    return res


def get_latest_build(url):
    with request.urlopen(url) as f:
        data = f.read()
        arr = [int(x) for x in re.findall(r'<a href="(\d+)', data.decode('utf8'))]
        arr.sort()
        return arr.pop()


def install_configure_ecp(controller_ip, runtime_config):
    _log.info("Applying runtime configuration in platform")
    last_status_code = None
    count_probes = 0
    res = None

    while (last_status_code is None or last_status_code == 503) and count_probes < 5: 
        res = requests.post(f"http://{controller_ip}:8080/api/v1/install/",
                            json=runtime_config)
        count_probes += 1
        last_status_code = res.status_code
        time.sleep(10)

    if res is None or res.status_code != 204:
        reason = res.reason if res is not None else "failed to make request"
        _log.error("failed to install platform with DF: " + reason)
        return False

    _log.info("successfully started installation process of platform")
    return True

def check_ecp_install_status(controller_ip):
    _log.info("Check platform install status.")
    install_state = "installing"
    status = False

    while install_state == "installing":
        res = requests.get(f"http://{controller_ip}:8080/api/v1/install/")
        if res.json()["install_state"] == "installed":
            _log.info("Platform is installed.")
            status = True
            break
        else:
            _log.info("Platform is still installing.")
        time.sleep(10)

    return status


def check_ecp_ui_status(controller_ip):
    _log.info("Check platform ui status.")
    last_status_code = None
    count_probes = 0
    res = None

    while (last_status_code is None or last_status_code == 503) and count_probes < 5:
        res = requests.get(f"http://{controller_ip}:8080/api/v1/install/")
        count_probes += 1
        last_status_code = res.status_code
        time.sleep(10)

    if res.status_code == 200:
        _log.info("Platform ui is up.")
        return True
    else:
        reason = res.reason if res is not None else "failed to make request"
        _log.error("failed to install platform ui: " + reason)
        return False






if __name__ == "__main__":
    #
    # Install BIN example
    #
    # os_install_and_bootstrap_platform([123, 123])

    #
    # Add credential example
    #
    # from core.cliobject import UserMachine
    # add_secrets(UserMachine('12.23.16.4', password=os.environ['host_passwd']), 'my-tenant')

    #
    # Trigger Jenkins JOB [ECP_build_and_deploy]
    #
    ips = ['16.143.21.125', '16.143.21.126', '16.143.21.122', '16.143.21.251', '16.143.22.154', '16.143.22.155', '16.143.21.124',
         '16.143.21.196', '16.0.14.82', '16.143.20.91', '16.143.21.127', '16.0.8.175', '16.143.21.66',
         '16.143.21.134', '16.143.21.197', '16.143.21.123']

    logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
    j = JenkinsAPI(jenkins_user='vivek', jenkins_token="118b4f82cb4fc241f5a17b0def2653c01e")
    #j.jenkins_os_install(ips)
    j.jenkins_get_os_build_by_id()

    # Get latest platform build
    #
    #latest_build = get_latest_build("http://bd-artifactory.mip.storage.hpecorp.net:80/artifactory/hpe-cp-eng-builds/debug/5.4/centos7")
    #print(f'Latest platform build is: {latest_build}')
