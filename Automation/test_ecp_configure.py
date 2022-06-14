import time
import socket
import logging

from urllib.parse import urlparse
import pytest

from core.platform_prepare import install_configure_ecp, check_ecp_ui_status, check_ecp_install_status

_log = logging.getLogger(__name__)

def test_ecp_ui_status(config):
    assert check_ecp_ui_status(config['controller_ip']) == True, 'Platform API is not running.'

@pytest.mark.skip
def test_install_ecp(config):
    runtime_config = config['runtime_configuration']
    assert install_configure_ecp(config['controller_ip'], runtime_config) == True, \
        "Applying Platform Runtime Configuration failed."


def test_check_ecp_status(config):
    assert check_ecp_install_status(config['controller_ip']) == True, \
        "Platofom Runtime Configuration is not installed."