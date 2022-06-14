import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.errorhandler import NoSuchElementException, ElementNotInteractableException

from core.pageobjects import BaseObject

_log = logging.getLogger(__name__)


class MinioPageObject(BaseObject):

    def do_login(self, login, password):
        res = True

        driver = self.driver
        driver.get(self._url)
        try:
            res &= self.set_input_field_by_id("accessKey", login)
            res &= self.set_input_field_by_id('secretKey', password)

            elem = driver.find_element(By.CLASS_NAME, "lw-btn")
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

    def create_bucket(self, bucket_name):
        btn = self.driver.find_element(By.ID, 'fe-action-toggle')
        btn.click()
        time.sleep(1)

        try:
            b2 = self.driver.find_element(By.ID, 'show-make-bucket')
            b2.click()
            time.sleep(1)
        except ElementNotInteractableException:
            return False

        f = self.driver.find_element(By.TAG_NAME, 'form')
        inp = f.find_element(By.CLASS_NAME, 'ig-text')
        inp.send_keys(bucket_name)
        inp.send_keys(Keys.RETURN)
        time.sleep(3)
        return True

    def verify_bucket_exists(self, bucket_name):
        sb = self.driver.find_element(By.ID, 'sidebar-toggle')
        if sb.is_displayed():
            sb.click()
            time.sleep(3)

        try:
            sb2 = self.driver.find_element(By.CLASS_NAME, 'fe-sidebar.toggled')
        except NoSuchElementException:
            sb2 = self.driver.find_element(By.CLASS_NAME, 'fesl-inner')

        if not sb2.is_displayed():
            return False

        ul = sb2.find_element(By.TAG_NAME, 'ul')
        for el in ul.find_elements(By.TAG_NAME, 'li'):
            if el.text == bucket_name:
                return True
        return False
