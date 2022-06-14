import pytest
import re
from core.pageobjects import NotebookPageObject
from selenium.webdriver.support.ui import WebDriverWait

import test_notebook

def test_open_xgboost1_example(config, driver):
    test_notebook.test_nb_login(config , driver)
    test_notebook.test_nb_open_example(config , driver)
    test_notebook.test_nb_restart_kernel(driver)
    test_notebook.test_nb_examples_init_vars(config , driver)

    test_notebook.pytest.notebook.open_url(test_notebook.pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/xgboost/XGB_income-test-concurrent.ipynb')


def test_run_xgboost1_example(driver):
    test_notebook.pytest.notebook.click_all_play()
    test_notebook.pytest.notebook.confirm_dialog()
    assert pytest.notebook.wait_output(r'Fitting \d+ folds for each of \d+ candidates, totalling \d+ fits'), 'No xgboost output'
    assert pytest.notebook.wait_output(r'Run time \(seconds\) \d+\.\d+'), 'No xgboost output'

def test_open_xgboost2_example(config , driver):
    test_notebook.pytest.notebook.open_url(test_notebook.pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/xgboost/XGB_income-test-sequential.ipynb')


def test_run_xgboost2_example(driver):
    test_notebook.pytest.notebook.click_all_play()
    test_notebook.pytest.notebook.confirm_dialog()
    assert pytest.notebook.wait_output(r'Fitting \d+ folds for each of \d+ candidates, totalling \d+ fits'), 'No xgboost output'
    assert pytest.notebook.wait_output(r'Run time \(seconds\) \d+\.\d+') , 'No xgboost output'
