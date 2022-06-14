import time
import socket
import logging

from urllib.parse import urlparse
import pytest

from core.cliobject import UserMachine
from core.platform_prepare import os_install

_log = logging.getLogger(__name__)



def test_jenkins_is_alive(config):
    jenkins = config['jenkins']
    url = jenkins['url']
    url_p = urlparse(url)
    url_port = url_p.port or 80
    remote_server = (url_p.hostname, url_port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_result = client_socket.connect_ex(remote_server)
    assert connect_result == 0, 'Jenkins server is down'


def test_os_install_trigger_job(config, host_passwd, ecp_jenkins_user, ecp_jenkins_token):
    ip_list = [config['controller_ip'], config['gateway_lb_ip']]
    ip_list += (config['hosts']['ip_list']).split(",")
    logging.info(ip_list)
    jenkins = config['jenkins'] if 'jenkins' in config else None
    jenkins_user = jenkins['user'] if jenkins and 'user' in jenkins else ecp_jenkins_user
    jenkins_token = jenkins['password'] if jenkins and 'password' in jenkins else ecp_jenkins_token
    assert jenkins_user is not None, 'Configuration error, please set ECP_JENKINS_USER in your evironment'
    assert jenkins_token is not None, 'Configuration error, please set ECP_JENKINS_TOKEN in your evironment'
    assert os_install(ip_list, jenkins['url'], jenkins_user,jenkins_token), 'Unable to finish external Jenkins JOB'