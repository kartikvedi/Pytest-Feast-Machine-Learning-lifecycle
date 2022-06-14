import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.errorhandler import StaleElementReferenceException, NoSuchElementException
from core.pageobjects import EzmeralPlatform

_log = logging.getLogger(__name__)


class AuthSettingsPageObject(EzmeralPlatform):
    def submit_form(self,auth):
        driver = self.driver
        #
        # Drop down menu
        #
        for b in driver.find_elements(By.TAG_NAME, 'button'):
            if 'Local' in b.text:
                b.click()
                break
        else:
            _log.warning('Directory Server drop down not found')
            #
            # Another try
            #
            for btn in driver.find_elements(By.TAG_NAME, 'button'):
                if 'Active Directory' in btn.get_attribute('title'):
                    btn.click()
                    break
            else:
                _log.error('Unable to find dropdown menu')
                return False
        time.sleep(1)

        #
        # Select LDAP from menu
        #
        dropdown = driver.find_element(
            By.CLASS_NAME, 'dropdown-menu.open.show')
        lis = dropdown.find_elements(By.TAG_NAME, 'li')
        for el in lis:
            if 'LDAP' in el.text:
                el.click()
                break
        else:
            assert 'Unable to found element with LDAP'
        time.sleep(2)

        main_div = driver.find_element(By.CLASS_NAME, 'ldap-ad-form')

        self.set_input_field_by_name('service_host', auth["service_host"], root=main_div)
        self.set_input_field_by_name('service_port', auth["service_port"], root=main_div)
        self.set_input_field_by_name('user_attribute', auth["user_attribute"], root=main_div)
        self.set_input_field_by_name('group_attribute', auth['group_attribute'], root=main_div)
        self.set_input_field_by_name('base_dn', auth['base_dn'], root=main_div)
        self.set_input_field_by_name('bind_dn', auth['bind_dn'], root=main_div)
        self.set_input_field_by_name('bind_pwd', auth['bind_pwd'], root=main_div)

        #
        # Select LDAPS security
        #
        drop_downs = main_div.find_elements(
            By.CLASS_NAME, 'btn dropdown-toggle btn-default'.replace(' ', '.'))
        for drop in drop_downs:
            drop.click()
            dropdown = driver.find_elements(
                By.CLASS_NAME, 'dropdown-menu.open.show')
            for el in dropdown:
                if 'LDAPS' in el.text:
                    el.click()
                    break
            break  # Because handle only one drop down menu, remove it if need to manage others

        # self.click_button('Submit')
        time.sleep(60)
    def open_verify_window(self):
        for _ in range(3):
            el = self.driver.find_element(By.ID, 'auth-settings-verify')
            try:
                for a in el.find_elements(By.TAG_NAME, 'a'):
                    if 'Verify' in a.text:
                        a.click()
                        time.sleep(3)
                        return True
            except StaleElementReferenceException:
                _log.warning('Unable to find verification window: StaleElementReferenceException')
            except NoSuchElementException:
                _log.warning('Unable to find verification window: NoSuchElementException')
            time.sleep(3)

        return False

    def verify_user(self, username, userpass):
        el = self.driver.find_element(By.ID, 'test_user_name')
        assert el, 'Unable to find user name field'
        el.send_keys(username)

        el = self.driver.find_element(By.ID, 'test_password')
        assert el, 'Unable to find user password field'
        el.send_keys(userpass)

        el = self.driver.find_element(By.ID, 'modal-form-submit')
        assert el, 'Unable to find submit button'
        el.click()
        time.sleep(3)
        el = self.driver.find_element(By.ID, 'auth-verification-result')
        if 'User authorized - settings are working' in el.text:
            return True
        return False
