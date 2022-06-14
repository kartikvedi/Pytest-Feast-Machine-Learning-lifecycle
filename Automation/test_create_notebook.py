import time
import logging
import pytest

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from core.pageobjects import EzmeralPlatform

_log = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def login_platform(config, driver):
    pytest.page = EzmeralPlatform(driver, url=config['url'] + '/bdswebui/k8stenant/notebooks/#kubedirector')
    pytest.page.do_login(config['login'], config['password'])


def test_notebook_exists(config):
    apps = pytest.page.get_endpoints_table()
    assert any(config['notebook']['name'] in s['name'] for s in apps) is False, 'Notebook already exists!'


def test_create_notebook(driver, config):
    # TODO: Add switching to proper Tenant

    notebook = config['notebook']
    description = 'nb-PyEZML-jenkins'
    driver.get(config['url'] + '/bdswebui/k8stenant/notebooks/#kubedirector')
    wait = WebDriverWait(driver, config['login_timeout_sec'])
    wait.until(lambda driver: "Notebook Page" in driver.title)
    btn_create_notebook = driver.find_element_by_xpath(
        '//*[@id="bdsApp"]/div/main/div[1]/div/div[2]/div[2]/div/div[1]/div[2]/div/a/span[1]')
    time.sleep(2)
    btn_create_notebook.click()
    time.sleep(1)
    _log.info(f'Title is: {driver.title}')
    wait = WebDriverWait(driver, config['login_timeout_sec'])
    wait.until(lambda driver: "Create Notebook" in driver.title)

    time.sleep(3)
    input_field_notebook_name = driver.find_element(By.ID, 'CreateEditK8sAppForm_label_metadata_name')
    input_field_notebook_name.click()
    input_field_notebook_name.send_keys(config['notebook']['name'])

    #
    # RAM memory
    #
    if 'ram' in notebook:
        ram = notebook['ram']
        time.sleep(2)
        sel_memory = driver.find_element(By.ID, 'CreateEditK8sAppForm_spec_roles_0_resources_requests_memory')
        sel_memory.click()
        sel_memory.send_keys(f'\b{ram}')
        description += f'-RAM{ram}G'

    #
    # Persistent storage memory
    #
    if 'pvc' in notebook:
        pvc = notebook['pvc']
        time.sleep(2)
        sel_persistent_storage_size = driver.find_element(By.ID, 'CreateEditK8sAppForm_spec_roles_0_storage_size')
        sel_persistent_storage_size.click()
        sel_persistent_storage_size.send_keys(f'\b{pvc}')
        description += f'-PVC{pvc}G'

    #
    # Description field
    #
    input_field_notebook_descr = driver.find_element(By.ID, 'CreateEditK8sAppForm_label_metadata_labels_description')
    input_field_notebook_descr.click()
    input_field_notebook_descr.send_keys(description)

    #
    # Associate with tenant
    #
    # select_assoc_tenant = driver.find_element(By.ID, 'CreateEditK8sAppForm_connections_clusters')
    # select_assoc_tenant.click()

    # select_assoc_tenant_input = driver.find_element(By.ID, 'CreateEditK8sAppForm_connections_clusters_input')
    # select_assoc_tenant.select_by_value('tr7')

    # xp = driver.find_element(By.XPATH, '//*[@id="menu-"]/div[3]/ul/li')
    # xp.click()
    notebook = config['notebook']
    time.sleep(1)
    if 'yaml_data' in notebook:
        _log.info('Editing YAML')
        pytest.page.open_yaml()
        for item in notebook['yaml_data']:
            _log.info('Section:' + item['section'])
            pytest.page.edit_yaml(item['section'], item['values'])

    pytest.page.click_button('Submit')
    time.sleep(5)
    assert driver.find_element(By.CLASS_NAME,
                               'MuiTypography-root.MuiTypography-h2'), 'Unable to submit form with notebook parameters'


def test_verify_notebook(config, driver):
    #
    # Common configs
    #
    app_conf = config['notebook']
    login = config['login']
    password = config['password']
    login_timeout = config['login_timeout_sec']

    #
    # Notebook configs
    #
    app_name = app_conf['name']
    creation_time_limit_seconds = app_conf['creation_max_timeout_seconds']

    #
    # Loop inside and check status
    #
    assert pytest.page.wait_creation_status_table(app_name, login, password, creation_time_limit_seconds,
                                                  login_timeout) is True, 'No successfully created notebook found'
