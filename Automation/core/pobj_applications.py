import time
import logging
from selenium.webdriver.common.by import By
from core.pageobjects import EzmeralPlatform

_log = logging.getLogger(__name__)

class ApplicationsPageObject(EzmeralPlatform):

    def click_on_app(self, app_name):
        for a in self.driver.find_elements(By.TAG_NAME, 'a'):
            if 'Launch' in a.text:
                href = a.get_property('href')
                if f'name={app_name}' in href:
                    a.click()
                    return True
        return False
