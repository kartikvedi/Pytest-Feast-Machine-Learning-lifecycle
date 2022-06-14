import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.errorhandler import StaleElementReferenceException, NoSuchElementException
from core.pageobjects import EzmeralPlatform

_log = logging.getLogger(__name__)


class AirGapSettingsPageObject(EzmeralPlatform):
    def submit_form(self, airgap_setting):
        airgap_setting = {
            "yum":{
                "base_url": "https://base_url",
                "repo_gpg_url": "https://repo_gpg_url",
                "rpm_gpg_url": "https://"
            },
            "registry": {
                "container_url": "https://container",
                "user_name":"abc",
                "password": "abc"
            }
        }
        driver = self.driver
        if "yum" in list(airgap_setting.keys()):
            for key in airgap_setting["yum"]:
                self.set_input_field_by_id(key,airgap_setting["yum"][key])
        if "registry" in list(airgap_setting.keys()):
            for key in airgap_setting["registry"]:
                self.set_input_field_by_id(key,airgap_setting["registry"][key])

        self.click_button('Submit')
