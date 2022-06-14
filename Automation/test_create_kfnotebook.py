import logging
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(ChromeDriverManager().install())
import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from core.pobj_applications import ApplicationsPageObject
from core.pobj_kf import KubeflowPageObject

_log = logging.getLogger(__name__)
kubeflow_url = None


def test_login(config, driver):
    pytest.page = ApplicationsPageObject(driver, url=config['url'] + '/bdswebui/k8stenant/dashboard')
    pytest.page.do_login(config['login'], config['password'])

def test_kf_dashboard_exists(config, driver):
    global kubeflow_url
    time.sleep(5)
    el = driver.find_element(By.XPATH,"//a[@id='#_sidebarLink']/span")
    assert el.text == 'Kubeflow Dashboard','Not able to find Kubeflow Dashboard'
    el = driver.find_element(By.XPATH, "//a[@id='#_sidebarLink']")
    # el.click()

def test_login_kubeflow(config,driver):
    kubeflow = KubeflowPageObject(driver, url = 'http://hpecp-10-1-100-147.rcc.local:10013/_/jupyter/?ns={}'.format(config['login']))
    kubeflow.do_login(config['login'], config['password'])
    driver.refresh()
    delay = 60
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'newResource')))
        myElem.click()
    except TimeoutException:
        _log.error("Unable to find out element")
