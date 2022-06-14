import time
import re
from core.pageobjects import NotebookPageObject
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import logging
import pytest

logging.basicConfig(filename='pytest.log', format='%(asctime)s  %(levelname)s:%(message)s', level=logging.INFO)
_log = logging.getLogger(__name__)

import test_notebook


def test_notebook_examples_kuberefresh(config, driver):
    test_notebook.test_nb_login(config, driver)
    test_notebook.wait(10)
    test_notebook.test_nb_open_example(config, driver)
    test_notebook.test_nb_restart_kernel(driver)
    test_notebook.test_nb_examples_init_vars(config, driver)
    test_notebook.test_nb_examples_kuberefresh(config, driver)

def test_notebook_examples_init(config, driver):
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/.test-examples-kf.ipynb')
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    pytest.notebook.click_play()    # import os
    pytest.notebook.click_play()    # def global variables
    pytest.notebook.click_play()    # Kubeflow
    pytest.notebook.click_play()    # set global variables

def test_notebook_examples_training(config, driver):
    pytest.notebook.click_play()    # run training
    assert pytest.notebook.wait_output(r'BLEU Score \(avg of BLUE 1-4\) on Holdout Set: \d+\.\d+', timeout=620), 'Not found training output'

def test_notebook_examples_env1(config, driver):
    pytest.notebook.click_play()    # set_env
    assert pytest.notebook.wait_output(r'env: NB_POD_NAME='), 'Not found set env variable'

def test_notebook_examples_env_seldon(config, driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'env: TEXT_PROCESSING_TEST_SELDON_DEPLOY_YAML_DATA='), 'Not found set env output'

def test_notebook_examples_met_condition(config, driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'pod/issue-summarization-example-' , timeout=600), 'Unable to met condition'

def test_notebook_examples_seldon_request(config, driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'{"data":{"names":\["t:0"],"ndarray":\[\["add support for for"]]},"meta":{}}'), 'Unable to execute seldon-request.py'

def test_notebook_examples_del_pod(config, driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(r'seldondeployment.machinelearning.seldon.io "issue-summarization" deleted'), 'Unable to delete pod'
