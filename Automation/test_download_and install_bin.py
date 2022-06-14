import time
import socket
import logging

from urllib.parse import urlparse
import pytest

from core.cliobject import UserMachine
from core.platform_prepare import download_and_install_platform_bin, uninstall_platform
from core.platform_prepare import install_configure_ecp, check_ecp_ui_status, check_ecp_install_status

_log = logging.getLogger(__name__)


def _get_controller_machine(config, host_passwd):
    ip = config['controller_ip']
    username = config['hosts']['user']
    return UserMachine(ip_address=ip, user=username, password=host_passwd)



@pytest.mark.skip
def test_uninstall_bin(config, host_passwd):
    assert host_passwd, 'Please define host_passwd in your ENV variables'
    controller_machine = _get_controller_machine(config, host_passwd)
    assert uninstall_platform(controller_machine), 'Uninstalling error, please check SSH execution logs'


def test_install_bin(config, host_passwd):
    assert host_passwd, 'Please define host_passwd in your ENV variables'
    controller_machine = _get_controller_machine(config, host_passwd)
    assert download_and_install_platform_bin(controller_machine, config['platform_bin_url'],
                                             config['password']), 'Unable to install platform BIN, please check SSH log'


