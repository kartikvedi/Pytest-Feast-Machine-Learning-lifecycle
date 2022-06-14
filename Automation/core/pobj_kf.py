import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.errorhandler import NoSuchElementException, ElementNotInteractableException

from core.pageobjects import BaseObject

_log = logging.getLogger(__name__)


class KubeflowPageObject(BaseObject):
    def do_login(self, login, password):
        res = True

        driver = self.driver
        driver.get(self._url)
        try:
            res &= self.set_input_field_by_id("login", login)
            res &= self.set_input_field_by_id('password', password)

            elem = driver.find_element(By.ID, "submit-login")
            elem.send_keys(Keys.RETURN)
            time.sleep(2)  # Web page need time to process request
            if driver.current_url != self._url:
                _log.info('Go back to the page before login')
                driver.get(self._url)
        except NoSuchElementException:
            #
            # Already logged in
            #
            pass

        return res
