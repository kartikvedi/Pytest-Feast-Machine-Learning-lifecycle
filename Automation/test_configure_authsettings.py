import pytest
import time

from core.pobj_authsettings import AuthSettingsPageObject


def test_login(driver, config):
    pytest.page = AuthSettingsPageObject(driver, url=config['url'] + '/bdswebui/authsettings')
    pytest.page.do_login('admin', config['password'])


def test_configure_authsettings(config, driver):
    """
        User Attribute
        Group Attribute
        Base DN
        Bind DN
        Bind Password
    """
    auth = config['auth']
    pytest.page.submit_form(auth)
    time.sleep(2)

def test_configure_authsettings_verify_user(config, driver):
    assert pytest.page.open_verify_window(), 'Unable to open verify window'
    assert pytest.page.verify_user(config['login'], config['password']), 'User verification failed'
