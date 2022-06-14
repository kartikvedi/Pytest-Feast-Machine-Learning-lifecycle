import pytest
import time

from core.pobj_airgap_settings import AirGapSettingsPageObject


def test_login(driver, config):
    pytest.page = AirGapSettingsPageObject(driver, url=config['url'] + '/bdswebui/gensettings/#airgap-settings')
    pytest.page.do_login('admin', config['password'])

def test_apply_airgap_settings(driver,config):
    pytest.page.submit_form(config)
