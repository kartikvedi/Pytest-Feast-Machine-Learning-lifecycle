import time
import logging
import pytest

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from core.pageobjects import EzmeralPlatform

_log = logging.getLogger(__name__)


def test_login(config, driver):
    pytest.page = EzmeralPlatform(driver, url=config['url'] + '/bdswebui/k8stenant/training/#kubedirector')
    pytest.page.do_login(config['login'], config['password'])


def test_create_training(config):
    app_conf = config['training']
    app_name = app_conf['name']
    assert pytest.page.click_button('Create Training') is True, 'Unable to find button for Create Training'
    time.sleep(5)  # Render form
    pytest.page.submit_app_form(app_name)


def test_verify_training(config, driver):
    #
    # Common configs
    #
    app_conf = config['training']
    login = config['login']
    password = config['password']
    login_timeout = config['login_timeout_sec']

    #
    # Training configs
    #
    app_name = app_conf['name']
    creation_time_limit_seconds = app_conf['creation_max_timeout_seconds']

    #
    # Loop inside and check status
    #
    assert pytest.page.wait_creation_status_table(app_name, login, password, creation_time_limit_seconds,
                                                  login_timeout) is True, 'No successfully created tenant found'
