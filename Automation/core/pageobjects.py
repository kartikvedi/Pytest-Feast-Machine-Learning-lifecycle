import time
import datetime
import re
import socket
import logging

import pandas as pd
from urllib.parse import urlparse
from transitions import Machine

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.errorhandler import NoSuchElementException, NoAlertPresentException, \
    StaleElementReferenceException, ElementNotInteractableException, ElementClickInterceptedException, \
    UnexpectedAlertPresentException
from selenium.webdriver.remote.webdriver import WebDriver

_log = logging.getLogger(__name__)


class BaseObject:

    def __init__(self, driver: WebDriver, url=None, max_response_timeout=120, admin_login=None, admin_password=None,
                 gw_ip=None, gw_hostname=None, host_passwd=None):
        self._driver = driver
        self._buttons = None
        self._kubernetes_version = None
        self._url = url
        self._gw_ip = gw_ip
        self._gw_hostname = gw_hostname
        self.max_response_timeout = max_response_timeout
        self._admin_login = admin_login
        self._admin_password = admin_password
        self._host_passwd = host_passwd

    @property
    def driver(self) -> WebDriver:
        return self._driver

    def set_input_field_by_id(self, field_name, value, retry=3, root=None):
        root = root or self.driver
        el = root.find_element(By.ID, field_name)
        for i in range(retry):
            el.click()
            el.clear()
            el.send_keys(value)
            if el.get_property('value') == value:
                break
            time.sleep(1)
        else:
            return False
        return True

    def set_input_field_by_name(self, field_name, value, retry=3, root=None):
        root = root or self.driver
        el = root.find_element(By.NAME, field_name)
        for i in range(retry):
            el.click()
            el.clear()
            el.send_keys(value)
            if el.get_property('value') == value:
                break
            time.sleep(1)
        else:
            return False
        return True

    def open_url(self, url, title=None):
        wait = WebDriverWait(self.driver, 15)
        self.driver.get(url)
        if title:
            wait.until(lambda driver: title in driver.title)

    def click_button(self, button_text):
        elements = self.driver.find_elements(By.TAG_NAME, 'button')
        _log.info(f'Found {len(elements)} button(s) on page')
        multi = len(elements) > 1
        for btn_el in elements:
            if button_text in btn_el.text:
                if multi and 'Mui-disabled' in btn_el.get_attribute('class'):
                    continue
                self.driver.execute_script("arguments[0].scrollIntoView();", btn_el)
                btn_el.click()
                time.sleep(3)
                return True

        #
        # Looks like buttons, but implemented as SPAN elements
        #
        for el in self.driver.find_elements(By.CLASS_NAME, 'MuiButton-label'):
            if button_text in el.text:
                self.driver.execute_script("arguments[0].scrollIntoView();", el)
                el.click()
                time.sleep(3)
                return True

        return False

    def get_table(self):
        tables = self.driver.find_elements(By.TAG_NAME, 'table')
        if len(tables):
            tbl = tables[0]
            try:
                pd_table = pd.read_html(tbl.get_attribute('outerHTML'))
            except StaleElementReferenceException:
                return None
            return pd_table
        return None

    def get_endpoints_table(self):
        table_data = []
        driver = self.driver
        notebook_endpoints_tab = driver.find_element(By.ID, 'tab_serviceEndpoints')
        notebook_endpoints_tab.click()
        time.sleep(3)  # Wait tab render
        #
        # Find and read table from page
        #
        apps_table = driver.find_element(By.XPATH,
                                         '//*[@id="bdsApp"]/div/main/div[1]/div/div[2]')
        rows = apps_table.find_elements(By.TAG_NAME, 'tr')
        for row in rows:
            column = row.find_elements(By.TAG_NAME, 'td')
            if len(column) > 3:
                app_name = column[3].text
                href_link = column[4].find_element(By.TAG_NAME, 'a').get_property('href')
                table_data.append({'name': app_name, 'url': href_link})
        return table_data

    def get_app_url(self, app_name):
        for app in self.get_endpoints_table():
            if app['name'] == app_name:
                return app['url']
        return None

    def catch_page_error503(self):
        try:
            el = self.driver.find_element(By.TAG_NAME, 'h1')
            if '503 Service Unavailable' in el.text:
                _log.error('Server error 503')
                return True
        except NoSuchElementException:
            pass
        return False

    def catch_splash_window(self):
        try:
            self.driver.find_element(By.ID, 'jupyterlab-splash')
            _log.warning('Splash window appears')
            return True
        except NoSuchElementException:
            pass
        return False

    def find_one_element(self, id_list):
        for el_id in id_list.split(','):
            try:
                el = self.driver.find_element(By.ID, el_id.strip())
                return el
            except NoSuchElementException:
                _log.warning(f'Unable to find element by id {el_id}')
        return None

    def one_click_by_id(self, id_list):
        """
        Click on the first element from the list
        :param id_list: Comma separated text string
        :return: bool
        """
        el = self.find_one_element(id_list)
        if el:
            el.click()
            return True
        return False


class EzmeralPlatform(BaseObject):
    transitions = [
        #
        # HTTP ready
        #
        {'trigger': 'ev_installing', 'source': 'st_ssh_connected', 'dest': 'st_http_inaccessible'},
        #
        # Init/Login
        #
        {'trigger': 'ev_http_connect', 'source': 'st_http_inaccessible', 'dest': 'st_http_ready',
         'conditions': 'http_connected'},
        {'trigger': 'ev_check_initial', 'source': 'st_http_ready', 'dest': 'st_initial',
         'conditions': 'do_check_initial'},
        {'trigger': 'ev_initial', 'source': 'st_initial', 'dest': 'st_initial_ready',
         'conditions': 'do_initial'},
        {'trigger': 'ev_logging_in', 'source': ['st_http_ready', 'st_initial_ready'], 'dest': 'st_do_auth',
         'conditions': 'do_auth'},
        #
        # Configure GW / LoadBalancer
        #
        {'trigger': 'ev_check_gw',
         'source': ['st_initial_ready', 'st_locked_down', 'st_gw_ready', 'st_do_auth', 'st_configure_gw_ready'],
         'dest': 'st_gw_ready', 'conditions': 'do_check_gw'},
        {'trigger': 'ev_configure_gw', 'source': 'st_locked_down', 'dest': 'st_configure_gw_ready',
         'conditions': 'do_configure_gw'},
        #
        # LockDown
        #
        {'trigger': 'ev_lockdown', 'source': 'st_do_auth', 'dest': 'st_locked_down', 'conditions': 'do_lockdown'},
        {'trigger': 'ev_exit_lockdown', 'source': ['st_locked_down', 'st_gw_ready'], 'dest': 'st_unlocked',
         'conditions': 'do_exit_lockdown'},
        {'trigger': 'ev_check_locked', 'source': ['st_do_auth', 'st_gw_ready'], 'dest': 'st_locked_down',
         'conditions': 'do_check_lock_down'},
    ]

    def __init__(self, *args, **kwargs):
        super(EzmeralPlatform, self).__init__(*args, **kwargs)
        self.machine = Machine(model=self,
                               states=['st_http_inaccessible', 'st_http_ready', 'st_do_auth',
                                       'st_locked_down', 'st_unlocked', 'st_gw_ready', 'st_initial',
                                       'st_initial_ready', 'st_configure_gw_ready'],
                               transitions=EzmeralPlatform.transitions, initial='st_http_inaccessible')
        self.driver.maximize_window()

    def do_login(self, login, password):
        res = True

        driver = self.driver
        driver.get(self._url)
        try:
            res &= self.set_input_field_by_id("id_username", login)
            res &= self.set_input_field_by_id('id_password', password)

            elem = driver.find_element(By.ID, "submitLogin")
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

    def wait_rows_status_by_column(self, column=None, value=None, timeout=300, count_limit=0):
        """
        Count matches by selected column name
        :param column: A name of table column
        :param value: Vale of status: ready/configured/error/etc...
        :param timeout: Stop searching after timeout seconds
        :param count_limit: Stop searching after limit records were found
        :return: int(count of rows)
        """
        if not value:
            _log.warning('No status selected for searching in table!')

        start_time = time.time()
        sleep_chunk = 5.0
        g_count = 0
        for i in range(int(timeout / sleep_chunk)):
            count = 0
            status_table = self.get_table()
            if status_table is None:
                _log.warning('Got an empty table for parsing, try again...')
                continue

            for j, row in status_table[0].iterrows():
                if value in row[column]:
                    _log.info(f'Found host {value} in table')
                    count += 1

            if count_limit and count == count_limit:
                _log.info('All hosts added, stop waiting')
                return count

            if start_time + timeout < time.time():
                _log.warning('Timeout exceeded')
                return count
            g_count = count
            time.sleep(sleep_chunk)
            _log.debug('Wait for 5 seconds...')

        return g_count

    def site_lockdown(self):
        driver = self.driver
        hover_menu = None
        for btn in driver.find_elements(By.TAG_NAME, 'button'):
            if btn.text == '' and btn.get_attribute('aria-haspopup') == 'true':
                hover_menu = btn
                break
        else:
            assert 'Unable to find hover menu'
        hover = ActionChains(driver).move_to_element(hover_menu)
        hover.perform()

        for div in driver.find_elements(By.TAG_NAME, 'li'):
            if 'Enter site lockdown' in div.text:
                if div.is_displayed():
                    div.click()
                    break
        else:
            assert 'Unable to find menu for site lockdown'

        self.click_button('Submit')  # TODO: Enter lock down reason in form

    def open_hover_menu(self):
        driver = self.driver
        hover_menu = None
        for btn in driver.find_elements(By.TAG_NAME, 'button'):
            if btn.text == '' and btn.get_attribute('aria-haspopup') == 'true':
                hover_menu = btn
                break
        else:
            assert 'Unable to find hover menu'
        hover = ActionChains(driver).move_to_element(hover_menu)
        hover.perform()

    @property
    def do_check_lock_down(self):
        driver = self.driver
        p = self
        p.open_hover_menu()
        for div in driver.find_elements(By.TAG_NAME, 'li'):
            if 'Exit site lockdown' in div.text:
                return True
        return False

    @property
    def do_exit_lockdown(self):
        driver = self.driver
        p = self
        p.open_hover_menu()
        for div in driver.find_elements(By.TAG_NAME, 'li'):
            if 'Exit site lockdown' in div.text:
                if div.is_displayed():
                    div.click()
                    return True
        return False

    @property
    def do_lockdown(self):
        p = self
        driver = self.driver
        p.open_hover_menu()
        for div in driver.find_elements(By.TAG_NAME, 'li'):
            if 'Enter site lockdown' in div.text:
                if div.is_displayed():
                    div.click()
                    break
        else:
            #
            # Unable to find menu for site lockdown
            #
            return False

        try:
            input_reason = driver.find_element(By.ID, 'siteLockDownForm_reason')
        except NoSuchElementException:
            _log.debug('Possible site already in lockDown mode')
            return False

        input_reason.click()
        input_reason.send_keys('AQA configure GW/LB')

        p.click_button('Submit')

        return True

    def do_auth(self):
        time.sleep(3)
        wait = WebDriverWait(self.driver, self.max_response_timeout)
        #
        # Open login page and wait for redirect to Gateway
        #
        self.do_login(self._admin_login, self._admin_password)
        time.sleep(3)
        wait.until(lambda driver: "Gateway" in driver.title)
        return True

    @property
    def http_connected(self):
        url_p = urlparse(self._url)
        url_port = url_p.port or 80
        remote_server = (url_p.netloc, url_port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect_result = client_socket.connect_ex(remote_server)
        if connect_result == 0:
            _log.info("HTTP Port is open")
            return True

        _log.info("HTTP Port is not open")
        return False

    @property
    def do_check_initial(self):
        """
        Check is it first login into web page.
        If it's true - this is a initial stage.
        :return: bool
        """
        _log.info('do_check_initial')
        #
        # Check is auth required on the first entrance
        #
        self.driver.get(self._url)
        time.sleep(5)
        if '/bdswebui/admininstall/' in self.driver.current_url:
            _log.info('do_check_initial -> Controller in initial state')
            return True
        _log.info('do_check_initial -> Controller not in initial state')
        return False

    def do_initial(self):
        driver = self.driver
        _log.info('do_initial')
        self.driver.get(self._url)  # Need force refresh, because 'Submit' is skipped.
        for i in range(500):

            #
            # Simulate mouse movement.
            # Result box will appears only with mouse events.
            #
            try:
                el = driver.find_element(By.ID, 'progress-title')  # 'HPE Ezmeral Runtime Enterprise Install Progress'
                _log.debug(el.text)
                action = ActionChains(driver)
                action.move_to_element(el)
                action.perform()
                action.move_by_offset(0, 0)
                action.perform()
            except NoSuchElementException:
                pass
            except ElementNotInteractableException:
                pass

            try:
                el = driver.find_element(By.CLASS_NAME, 'bootbox-body')
            except NoSuchElementException:
                _log.warning('Not found element bootbox-body')
                time.sleep(10)
                continue

            if el.is_displayed():
                if 'HPE Ezmeral Runtime Enterprise setup completed successfully' in el.text:
                    return True
            _log.info('Another try...')
            time.sleep(10)
        else:
            _log.warning(
                'Unable to complete installation, box "HPE Ezmeral Runtime Enterprise setup completed successfully" not found')
        return False

    def submit_app_form(self, app_name, load_page_timeout=15):
        """
        Fill Application form
        """
        wait = WebDriverWait(self.driver, load_page_timeout)
        wait.until(lambda driver: driver.find_element(By.ID, 'CreateEditK8sAppForm_label_metadata_name'))
        try:
            elem = self.driver.find_element(By.ID, "CreateEditK8sAppForm_label_metadata_name")
            elem.send_keys(app_name)
            self.click_button('Submit')
        except NoSuchElementException:
            return False
        return True

    def open_yaml(self):
        try:
            btn_edit_yaml = self.driver.find_element(By.XPATH, '//*[@id="bdsApp"]/div/main/div[1]/div/form/div[2]/div/button[1]')
        except NoSuchElementException:
            return False
        time.sleep(1)
        btn_edit_yaml.click()
        time.sleep(1)
        return True

    def edit_yaml(self, search_string, input_values):
        driver = self.driver
        content = driver.find_element(By.CLASS_NAME, 'ace_layer.ace_text-layer')
        rows = content.find_elements(By.CLASS_NAME, 'ace_line')
        i = 0
        for row in rows:
            if re.search(search_string, row.text):
                driver.find_elements(By.CLASS_NAME, 'ace_gutter-cell')[i].click()
                action = ActionChains(driver)
                action.send_keys(Keys.END)
                if '[]' in row.text:
                    action.send_keys(Keys.BACKSPACE)
                    action.send_keys(Keys.BACKSPACE)
                action.send_keys(Keys.RETURN)
                action.send_keys('\t')
                for str_i in range(len(input_values)):
                    action.send_keys(input_values[str_i])
                    if str_i + 1 < len(input_values):  # Do not send Enter on the last value entered
                        action.send_keys(Keys.RETURN)
                action.perform()
                return True
            i += 1
        else:
            _log.warning('Unable to find string for text input')
        return False

    def switch_to_application_tab(self, login_timeout):
        driver = self.driver
        wait = WebDriverWait(driver, login_timeout)
        _log.info(f'Current title is: "{driver.title}", expected "Application Page"')
        wait.until(lambda driver: driver.find_element(By.ID, 'tab_kubedirector'))
        _log.info(f'Title after waiting: "{driver.title}"')
        apps_endpoint_tab = driver.find_element(By.ID, 'tab_kubedirector')
        apps_endpoint_tab.click()
        time.sleep(3)  # Wait tab render

    def wait_creation_status_table(self, app_name, login, password, creation_time_limit_seconds=300, login_timeout=60):
        deadline = datetime.datetime.now() + datetime.timedelta(seconds=creation_time_limit_seconds)
        no_tables_counter = 0
        no_app_found_counter = 0
        _log.info(f'Wait to finish creating application: {app_name}')
        self.switch_to_application_tab(login_timeout)
        while datetime.datetime.now() < deadline:
            #
            # Check loop errors
            #
            if no_tables_counter > 3:
                _log.error('Unable to find table on page')
                return False
            if no_app_found_counter > 3:
                _log.error('Unable to find application by name in table')
                return False

            #
            # Find tables on screen
            #
            tables = self.get_table()
            if tables is None:
                _log.warning('No tables found, re-login')
                self.do_login(login, password)
                self.switch_to_application_tab(login_timeout)
                no_tables_counter += 1
                time.sleep(5)
                continue

            #
            # Parse table with application status
            #
            st = None
            for table in tables:
                for idx, row in table.iterrows():
                    if row['Name'] == app_name:
                        st = row['Status']
                        if st == 'creating':
                            _log.debug('Creating in progress...')
                        if st == 'configured':
                            _log.info('Creation finished.')
                            return True
                        if st == 'deleting':
                            _log.warning('Application will be deleted')
                        break  # Goto next timer loop
                else:
                    no_app_found_counter += 1

            _log.info(f'Try again, time left: {deadline - datetime.datetime.now()}, status: {st}')
            time.sleep(60)

        _log.error('Application creation time limit exceeded')
        return False


class GWPageObject(EzmeralPlatform):

    def submit_form(self, hostname, ip_addr, password):
        res = True
        self.driver.find_element(By.ID, 'bdsApp').click()  # Close Hover
        time.sleep(5)  # TODO: Disappear Hover Menu

        res &= self.set_input_field_by_id("gateway-add-form_worker_ip", ip_addr)
        res &= self.set_input_field_by_id('gateway-add-form_host_name', hostname)
        res &= self.set_input_field_by_id('gateway-add-form_ssh_cred_type_password', password)

        elem = self.driver.find_element(By.ID, "gateway-add-form_submitBtn")
        elem.click()

        time.sleep(3)  # Web page need time to process request

        return res

    @property
    def do_configure_gw(self):
        gw = self
        gw.open_url(self._url)
        gw.submit_form(self._gw_hostname, self._gw_ip, self._host_passwd)
        return True

    @property
    def do_check_gw(self):
        gw = self
        gw.open_url(self._url)
        no_rows_count = 0
        for g in range(500):
            status_table = gw.get_table()
            if status_table:
                for i, row in status_table[0].iterrows():
                    if row['Status'] == 'error':
                        assert 'Error configure gateway'
                    if row['Status'] == 'Sorry, no matching records found':
                        _log.warning('No records found!')
                        if no_rows_count > 1:
                            _log.warning('No records limit errors reached. Stop scanning!')
                            return False
                        no_rows_count += 1
                    if row['Status'] == 'installed':
                        return True
                    if row['Status'] == 'running bundle':
                        pass
                    if row['Status'] == 'decommission_in_progress':
                        pass
                    if row['Status'] == 'delete in progress':
                        pass
                    if row['Status'] == 'installing':
                        pass
                    if row['Status'] == 'prechecks error':
                        _log.warning('Gateway -> prechecks error detected!')
                        return False
                    if row['Status'] == 'error':
                        _log.warning('Gateway -> error status detected!')
                        return False
                    time.sleep(10)

            time.sleep(5)
        _log.warning('Gateway -> overall check failed.')
        return False


class TenantPageObject(EzmeralPlatform):

    def create_tenant(self, tenant_name, ns_name, tenant_descr, cores, ext_auth_role='Admin', ext_auth='', adopt_existing=False):
        self.click_button('Create')
        self.set_input_field_by_id('name', tenant_name)
        self.set_input_field_by_id('specified_namespace_name', ns_name)
        self.set_input_field_by_id('description', tenant_descr)
        chk_ml_ops_project = self.driver.find_element(By.ID, 'ml_project')
        chk_ml_ops_project.click()
        self.set_input_field_by_id('cores', cores)

        try:
            tab_ext_auth = self.driver.find_element(By.ID, 'external_auth_tab')
            tab_ext_auth.click()
            ext_group = self.driver.find_element(By.ID, 'external_groups_block')
            inp_auth = ext_group.find_element(By.NAME, 'extgroups')
            inp_auth.send_keys(ext_auth)
            btn = ext_group.find_element(By.TAG_NAME, 'button')
            btn.click()
            ul = ext_group.find_element(By.TAG_NAME, 'ul')
            for li in ul.find_elements(By.TAG_NAME, 'li'):
                if ext_auth_role in li.text:
                    li.click()
                    break
            if adopt_existing:
                chk_adopt_existing_namespace = self.driver.find_element(By.ID, 'adopt_existing_namespace')
                chk_adopt_existing_namespace.click()

                div_cluster_services_group = self.driver.find_element(By.XPATH, "//select[@id='cluster_services_select']/..")
                btn_cluster_services = div_cluster_services_group.find_element(By.TAG_NAME, 'button')
                btn_cluster_services.click()
                ul_cluster_services = div_cluster_services_group.find_element(By.TAG_NAME, 'ul')
                for li in ul_cluster_services.find_elements(By.TAG_NAME, 'li'):
                    if ns_name == li.text:
                        li.click()
                        break
        except NoSuchElementException:
            _log.warning('Unable to find tab with external auth!')

        self.click_button('Submit')

    def switch_to_tenant(self, tenant_name):
        t = self.driver.find_element(By.TAG_NAME, 'table')
        rows = t.find_elements(By.TAG_NAME, 'tr')
        for row in rows[1:]:
            tds = row.find_elements(By.TAG_NAME, 'td')
            for td in tds:
                if tenant_name in td.text:
                    for span in td.find_elements(By.TAG_NAME, 'span'):
                        if span.is_enabled():
                            span.click()
                            return True
        return False

    def assign_user(self, user_name, role):
        driver = self.driver
        #
        # Click 'Assign'
        #
        btn_assign = driver.find_element(By.ID, 'userAssignBtn')
        if btn_assign:
            btn_assign.click()
            time.sleep(3)
        else:
            return False

        #
        # Select user
        #
        for row in driver.find_elements(By.CLASS_NAME,
                                        'MuiButtonBase-root MuiListItem-root list-item MuiListItem-gutters MuiListItem-button'.replace(
                                            ' ', '.')):
            if row.text == user_name:
                row.click()
                break
        else:
            return False

        #
        # Select role for user
        #
        blocks = driver.find_elements(By.CLASS_NAME,
                                      'MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 MuiGrid-grid-md-true'.replace(' ',
                                                                                                                  '.'))
        for el in blocks[1].find_elements(By.TAG_NAME, 'span'):
            if role in el.text:
                el.click()
                break
        else:
            return False

        buttons = blocks[1].find_elements(By.TAG_NAME, 'button')
        for b in buttons:
            if 'Save' in b.text:
                b.click()
                break
        else:
            return False
        return True


class AddUserPageObject(EzmeralPlatform):
    def set_external_user(self):
        chk_is_external = self.driver.find_element(By.ID, 'is_external')
        chk_is_external.click()
        pass


class ClustersPageObject(EzmeralPlatform):
    def enable_host(self, host_name, selector_id=0):
        # Re-read selector, cause some item moved
        selector = self.driver.find_elements(By.CLASS_NAME, 'listSelectorWrapper')
        for el in selector[selector_id].find_elements(By.TAG_NAME, 'li'):
            # if 'Move all filtered items' in div.text:
            #     div.click()
            #     break
            if re.search(host_name, el.text):
                # Fire on all div layers
                for div in el.find_elements(By.TAG_NAME, 'div'):
                    try:
                        div.click()
                        break
                    except ElementClickInterceptedException:
                        pass
                time.sleep(1)
                return True
        return False

    def configure_auth(self, auth_type='LDAP', security='LDAPS', service_host='bd-389ds-ldap1.mip.storage.hpecorp.net',
                       service_port='636', user_attribute='cn', base_dn='dc=mip,dc=storage,dc=hpecorp,dc=net',
                       bind_dn='cn=admin,dc=mip,dc=storage,dc=hpecorp,dc=net', bind_pwd='admin123'):
        driver = self.driver
        driver.find_element(By.CLASS_NAME,
                            'MuiInputBase-root MuiOutlinedInput-root MuiInputBase-formControl'.replace(' ',
                                                                                                       '.')).click()
        time.sleep(1)
        for el in driver.find_elements(By.CLASS_NAME,
                                       'MuiButtonBase-root MuiListItem-root MuiMenuItem-root MuiMenuItem-gutters MuiListItem-gutters MuiListItem-button'.replace(
                                           ' ', '.')):
            if auth_type in el.text:
                el.click()
                break
            time.sleep(1)

        time.sleep(1)

        el = driver.find_element(By.ID, 'AuthenticationForm_security_protocol')
        el.click()
        time.sleep(1)
        for x in driver.find_elements(By.CLASS_NAME,
                                      'MuiButtonBase-root MuiListItem-root MuiMenuItem-root MuiMenuItem-gutters MuiListItem-gutters MuiListItem-button'.replace(
                                          ' ', '.')):
            if security in x.text:
                x.click()
                break
            time.sleep(1)
        driver.find_element(By.ID, 'AuthenticationForm_auth_service_locations_0_host').send_keys(service_host)
        driver.find_element(By.ID, 'AuthenticationForm_auth_service_locations_0_port').send_keys(service_port)
        driver.find_element(By.ID, 'AuthenticationForm_user_attribute').send_keys(user_attribute)
        driver.find_element(By.ID, 'AuthenticationForm_base_dn').send_keys(base_dn)
        driver.find_element(By.ID, 'AuthenticationForm_bind_dn').send_keys(bind_dn)
        driver.find_element(By.ID, 'AuthenticationForm_bind_pwd').send_keys(bind_pwd)

    def configure_app(self, istio=False, kubeflow=False):
        driver = self.driver
        if kubeflow:
            driver.find_element(
                By.ID, 'ApplicationConfigurationForm_addons_kubeflow').click()
        if istio:
            driver.find_element(
                By.ID, 'ApplicationConfigurationForm_addons_istio').click()

    def dropdown_kubernetes_versions(self, version_value):
        """
        Return: list: []
        """
        versions = []

        #
        # Drop down list
        #
        self.one_click_by_id('ClusterHostConfigurationForm_k8s_version, ClusterConfigurationForm_k8s_version')

        #
        # UL
        #
        ul = self.driver.find_element(By.CLASS_NAME, 'MuiList-root.MuiMenu-list.MuiList-padding')

        #
        # Go though version list and click on required value
        #
        for li in ul.find_elements(By.TAG_NAME, 'li'):
            current_version = li.text.strip()
            versions.append(current_version)

        #
        # Select desired version
        #
        for li in ul.find_elements(By.TAG_NAME, 'li'):
            current_version = li.text.strip()
            if version_value in current_version:
                li.click()
                self._kubernetes_version = current_version
                break

        return versions

    @property
    def kubernetes_version(self):
        if not self._kubernetes_version:
            self._kubernetes_version = self.find_one_element(
                'ClusterHostConfigurationForm_k8s_version, ClusterConfigurationForm_k8s_version').text
        return self._kubernetes_version

    @kubernetes_version.setter
    def kubernetes_version(self, value):
        self.dropdown_kubernetes_versions(value)


class NotebookPageObject(EzmeralPlatform):

    @property
    def buttons(self):
        return self._buttons

    @buttons.setter
    def buttons(self, value):
        self._buttons = value

    def _load_toolbar(self):
        toolbar = None
        found_toolbar = False
        for i in range(40):
            try:
                for toolbar in self.driver.find_elements(By.CLASS_NAME,
                                                         'lm-Widget p-Widget jp-Toolbar jp-scrollbar-tiny jp-NotebookPanel-toolbar'.replace(
                                                             ' ', '.')):
                    if toolbar.is_displayed():
                        found_toolbar = True
                        break
            except NoSuchElementException:
                pass
            except UnexpectedAlertPresentException:
                self.driver.switch_to.alert.accept()

            self.catch_splash_window()
            if found_toolbar:
                break
            time.sleep(5)
            # TODO: Add max_response_timeout handler
        else:
            assert 'Unable to find toolbar in Notebook'

        self._buttons = toolbar.find_elements(By.CLASS_NAME,
                                              'bp3-button bp3-minimal jp-ToolbarButtonComponent minimal jp-Button'.replace(
                                                  ' ', '.'))

    def open_url(self, url, title=None):
        self.driver.get(url)
        try:
            self.driver.switch_to.alert.accept()
        except NoAlertPresentException:
            pass
        time.sleep(30)  # TODO: Remove after fixing EZML-749
        # opened_tabs = driver.find_elements(By.CLASS_NAME, 'lm-TabBar-tabLabel.p-TabBar-tabLabel')
        self._load_toolbar()

    def do_login(self, login, password):
        driver = self.driver
        driver.get(self._url)
        for i in range(3):
            try:
                elem = driver.find_element(By.ID, "username_input")
                break
            except NoSuchElementException:
                _log.warning('No login input field found')
                time.sleep(5)

            assert self.catch_page_error503() is False, 'Error 503 on page found'
            self.catch_splash_window()

        else:
            return False

        elem.send_keys(login)
        elem = driver.find_element(By.ID, "password_input")
        elem.send_keys(password)
        elem = driver.find_element(By.ID, "login_submit")
        elem.send_keys(Keys.RETURN)

        for i in range(100):
            try:
                driver.find_element(By.ID, "jp-top-panel")
                _log.info('Login success')
                time.sleep(2)  # Wait full page is load
                return True
            except NoSuchElementException:
                _log.warning(f'Panel is not ready yet, try {i + 1} of 100...')
            assert self.catch_page_error503() is False, 'Error 503 on page found'
            self.catch_splash_window()
            time.sleep(5)
        _log.warning('Login failed')
        return False

    def _click_toolbar_button(self, button_id, title=None, timeout=2):
        button = self._buttons[button_id]
        _log.info(button)
        performed_refresh = False
        #
        # Reload toolbar if button is not appears
        #
        if not button.is_displayed():
            self._load_toolbar()
            time.sleep(10)

        if title:
            assert title in button.get_attribute('title')

        for _ in range(5):
            try:
                if button.is_enabled() is True and button.is_displayed() is True:
                    button.click()
                    time.sleep(5)
                    self.confirm_dialog()
                    break
            except UnexpectedAlertPresentException:
                _log.warning('UnexpectedAlertPresentException :: switch_to.alert.accept')
                self.driver.switch_to.alert.accept()
            except ElementClickInterceptedException:
                if not performed_refresh:
                    _log.warning('ElementClickInterceptedException :: Page will refreshed')
                    self.driver.refresh()
                    performed_refresh = True
                    time.sleep(20)  # TODO: Detect page is finished load
                else:
                    _log.warning('Page already refreshed')
                _log.warning('ElementClickInterceptedException :: Reload toolbar')
                self._load_toolbar()
            except ElementNotInteractableException:
                _log.warning('ElementNotInteractableException :: Reload toolbar')
                self._load_toolbar()
            except StaleElementReferenceException:
                if not performed_refresh:
                    _log.warning('StaleElementReferenceException :: Page will refreshed')
                    self.driver.refresh()
                    performed_refresh = True
                    time.sleep(20)  # TODO: Detect page is finished load
                else:
                    _log.warning('Page already refreshed')
            time.sleep(5)

        time.sleep(timeout)  # Wait browser proceed request

    def click_play(self, timeout=2):
        self._click_toolbar_button(5, 'Run the selected cells', timeout=timeout)

    def click_save(self, timeout=2):
        self._click_toolbar_button(0, 'Save the notebook contents', timeout)

    def click_restart_kernel(self, timeout=2):
        self._click_toolbar_button(7, 'Restart the kernel', timeout)

    def click_all_play(self):
        self._click_toolbar_button(8, 'Restart the kernel, then re-run the whole notebook')

    def confirm_dialog(self):
        driver = self.driver
        for _ in range(5):
            try:
                btn_restart = driver.find_element(By.CLASS_NAME,
                                                  'jp-Dialog-button jp-mod-accept jp-mod-warn jp-mod-styled'.replace(
                                                      ' ', '.'))
                break
            except NoSuchElementException:
                time.sleep(2)
        else:
            return False

        if btn_restart.is_displayed():
            btn_restart.click()
            time.sleep(5)
            return True

        return False

    def get_output_arr(self):
        output = self.driver.find_elements(By.CLASS_NAME,
                                           'lm-Widget p-Widget jp-RenderedText jp-mod-trusted jp-OutputArea-output'.replace(
                                               ' ', '.'))
        return output

    def wait_output(self, value, timeout=None):
        timeout = timeout or self.max_response_timeout
        start_seconds = time.time()
        for i in range(int(timeout / 4.0)):
            #
            # Search expected text
            #
            if any(re.search(value, s.text) for s in self.get_output_arr()):
                break
            if start_seconds + timeout < time.time():
                return False
            time.sleep(4)
        else:
            return False

        for i in range(int(timeout / 4.0)):
            #
            # Wait to asterisk is gone
            #
            if any(re.search(r'\[\*]', s.text) for s in self.driver.find_elements(By.CLASS_NAME,
                                                                                  'lm-Widget p-Widget jp-InputPrompt jp-InputArea-prompt'.replace(
                                                                                      ' ',
                                                                                      '.'))):
                time.sleep(4)
            else:  # No asterisk found, all jobs is done
                return True
            if start_seconds + timeout < time.time():
                return False
        return False

    def authorize_inside_nb(self, password):
        driver = self.driver
        elem = driver.find_element(By.CLASS_NAME, "jp-Stdin-input")
        elem.send_keys(password)
        elem.send_keys(Keys.RETURN)

    def set_cert_inside_nb(self, login):
        driver = self.driver
        elem = driver.find_element(By.CLASS_NAME, "jp-Stdin-input")
        elem.send_keys("/home/" + login + "/ca.cert")
        elem.send_keys(Keys.RETURN)

    def is_there_an_error_in_notebook(self):
        driver = self.driver
        try:
            driver.find_element(By.XPATH,
                                "//div[@class='lm-Widget p-Widget jp-RenderedText jp-mod-trusted jp-OutputArea-output' and @data-mime-type='application/vnd.jupyter.stderr' and not(ancestor::div[contains(@class, 'lm-mod-hidden')])]")
        except NoSuchElementException:
            return False
        return True

    def wait_for_output_of_the_current_cell(self, timeout=None):
        driver = self.driver
        timeout = timeout or self.max_response_timeout
        start_seconds = time.time()
        while True:
            elem = driver.find_element(By.XPATH,
                                       "//div[contains(@class, 'jp-Cell') and contains(@class, 'jp-mod-selected')]/preceding-sibling::div[1]/div[contains(@class, 'jp-Cell-inputWrapper')]/div[contains(@class, 'jp-Cell-inputArea')]/div[contains(@class, 'jp-InputArea-prompt')]")
            if elem.get_attribute("innerHTML") != '[*]:':
                break
            if start_seconds + timeout < time.time():
                return None
            time.sleep(2)
        try:
            elem = driver.find_element(By.XPATH,
                                       "//div[contains(@class, 'jp-Cell') and contains(@class, 'jp-mod-selected')]/preceding-sibling::div[1]/div[contains(@class, 'jp-Cell-outputWrapper')]/div[contains(@class, 'jp-Cell-outputArea')]/div[contains(@class, 'jp-OutputArea-child')]/div[contains(@class, 'jp-OutputArea-output')]/pre")
        except NoSuchElementException:
            return ""
        return elem.get_attribute("innerHTML")

    def replace_line_in_cell_after_header(self, value, header_id, cell_offset=1, line_offset=0):
        """Replace a line of text in Notebook cell that is below the header.

        Args:
            value (str): String that will replace text in specified line of target cell
            header_id (str): Header's ID from with will be conted offset to edit cell
            cell_offset (int): Offset for target cell:
                                  0 means the header itself
                                  1 - cell just bellow the header (default)
            line_offset (int): line offest inside cell:
                                  0 means the first line in cell (default)
                                  1 - second line in cell
        """
        self.select_cell_after_header(header_id, cell_offset)
        self.replace_line_in_current_cell(value, line_offset)

    def select_cell_after_header(self, header_id, cell_offset=1):
        driver = self.driver
        # Find header cell
        section = driver.find_element(By.ID, header_id)
        section.click()
        # wait(1)

        # Move to target cell
        action = ActionChains(driver)
        for _ in range(cell_offset):
            action.send_keys(Keys.ARROW_DOWN)
        action.perform()

    def replace_line_in_current_cell(self, value, line_offset=0):
        action = ActionChains(self.driver)

        # Enter editing cell
        action.send_keys(Keys.RETURN)

        # Go to the beginning of current cell
        action.key_down(Keys.CONTROL)
        action.send_keys(Keys.HOME)
        action.key_up(Keys.CONTROL)
        action.perform()

        # Go to target line inside cell
        for _ in range(line_offset):
            action.send_keys(Keys.ARROW_DOWN)
        action.perform()

        # Select all text in current line
        action.send_keys(Keys.HOME)
        action.key_down(Keys.SHIFT)
        action.send_keys(Keys.END)
        action.key_up(Keys.SHIFT)
        action.perform()

        # Delete all text in current line
        action.send_keys(Keys.DELETE)
        action.perform()

        # input value into current line
        action.send_keys(value)
        action.perform()

    def click_by_xpath(self, xpath):
        driver = self.driver
        el = driver.find_element(By.XPATH, xpath)
        el.click()
        time.sleep(2)

    def click_running_tab(self):
        self.click_by_xpath('/html/body/div/div[3]/div[1]/ul/li[2]')
        time.sleep(2)

    def click_file_browser_tab(self):
        self.click_by_xpath('/html/body/div/div[3]/div[1]/ul/li[1]')
        time.sleep(2)

    def close_kernel_sessions(self):
        self.click_file_browser_tab()
        self.click_file_browser_tab()
        self.click_running_tab()
        self.click_by_xpath('/html/body/div/div[3]/div[2]/div[1]/div[3]/div[2]/header/button')
        self.confirm_dialog()
        time.sleep(1)



class HostsPageObject(EzmeralPlatform):

    def click_by_xpath(self, xpath):
        driver = self.driver
        el = driver.find_element(By.XPATH, xpath)
        el.click()
        time.sleep(2)

    def submit_form(self, ip_list, password, datafabric=False):
        """
        IP format List:
            192.168.162.1
            192.168.162.1,12,76,192.162.168.12
            192.168.162.1-12
            10.1.10.1-12,15,192.162.168.12-15
        """
        res = self.set_input_field_by_id("k8shost-add_worker_ip", ip_list)
        res &= self.set_input_field_by_id(
            'k8shost-add_ssh_cred_type_password', password)
        if datafabric:
            element = self.driver.find_element(By.ID, "k8shost-add_tags_0_tag_id")
            actions = ActionChains(self.driver)
            actions.move_to_element(element).click_and_hold().perform()
            element = self.driver.find_element(By.CSS_SELECTOR, "#menu- > div:nth-child(1)")
            actions = ActionChains(self.driver)
            actions.move_to_element(element).release().perform()
            self.driver.find_element(By.CSS_SELECTOR, "body").click()
            self.driver.find_element(By.CSS_SELECTOR, ".MuiMenuItem-root:nth-child(3)").click()
            self.driver.find_element(By.CSS_SELECTOR, ".K8sHostsAddPage").click()
            res &= self.set_input_field_by_id("k8shost-add_tags_0_tag_value", "true")

        elem = self.driver.find_element(By.ID, "k8shost-add_submitBtn")
        elem.send_keys(Keys.RETURN)
        return res



    def select_hosts(self, host_list=None, with_status=None, click=True):
        tbl = self.driver.find_element(By.TAG_NAME, 'table')
        res_host_list = []
        #
        # Select hosts one-by-one
        #
        for row in tbl.find_elements(By.TAG_NAME, 'tr'):
            tds = row.find_elements(By.TAG_NAME, 'td')
            if len(tds) > 5:
                #
                # With status
                #
                if with_status:
                    if with_status not in tds[6].text:
                        logging.info(tds[6].text)
                        continue

                #
                # Host list
                #
                if host_list:
                    m = re.findall(r'[0-9]+(?:\.[0-9]+){3}', tds[1].text)
                    if m:
                        ipaddress = m[0].strip()
                        if ipaddress != '' and ipaddress in host_list:
                            res_host_list.append(ipaddress)
                            #
                            # Click
                            #
                            if click:
                                f_input = tds[0].find_element(By.TAG_NAME, 'input')
                                f_input.click()
                    continue
                #
                # Click without host name
                #
                if click:
                    f_input = tds[0].find_element(By.TAG_NAME, 'input')
                    f_input.click()

                #
                # Add IP (no hostname available)
                #
                res_host_list.append(tds[1].text.strip())
        return res_host_list

    def install_hosts(self):
        driver = self.driver
        tbl = driver.find_element(By.TAG_NAME, 'table')
        #
        # Select all
        #
        th = tbl.find_elements(By.TAG_NAME, 'th')[0]
        inp = th.find_element(By.TAG_NAME, 'input')
        # inp.click()

        btn_install = driver.find_element(By.ID, 'k8sHostInstallBtn')
        btn_install.click()

        for btn_Ok in driver.find_elements(By.TAG_NAME, 'button'):
            if btn_Ok.text == 'Ok' and btn_Ok.is_enabled():
                btn_Ok.click()
                break
            else:
                assert 'Unable to confirm hosts installation'

    def delete_hosts(self, host_list):
        driver = self.driver
        tbl = driver.find_element(By.TAG_NAME, 'table')
        #
        # Select all
        #
        th = tbl.find_elements(By.TAG_NAME, 'th')[0]
        inp = th.find_element(By.TAG_NAME, 'input')
        # inp.click()

        self.select_hosts(tbl, host_list)
        btn_install = driver.find_element(By.ID, 'k8sHostDeleteBtn')
        btn_install.click()

        for btn_Ok in driver.find_elements(By.TAG_NAME, 'button'):
            if btn_Ok.text == 'Ok' and btn_Ok.is_enabled():
                btn_Ok.click()
                break
            else:
                assert 'Unable to confirm hosts installation'
