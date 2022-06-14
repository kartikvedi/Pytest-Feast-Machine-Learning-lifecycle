import time
import pytest
from core.pageobjects import EzmeralPlatform, NotebookPageObject
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import test_notebook
import re


def test_open_mlflow_example(config, driver):
    test_notebook.test_nb_login(config, driver)

    test_notebook.pytest.notebook.open_url(
        test_notebook.pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/mlflow/mlflow_example.ipynb')
    test_notebook.test_nb_restart_kernel(driver)


def test_mlflow_kuberefresh(config, driver):
    #
    # set_kubeconfig
    #
    pytest.notebook.replace_line_in_cell_after_header(f"PASSWORD = '{config['password']}'", 'MLflow-Tutorial', 2, 4)
    pytest.notebook.click_play()
    if "Service account might be improperly set" in pytest.notebook.wait_for_output_of_the_current_cell():
        pytest.notebook.select_cell_after_header('MLflow-Tutorial', 2)
        pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == f'Valid user\nkubeconfig set for user {config["login"]}\n', 'Unable to set Kubeflow section variables'


def test_mlflow_load(config, driver):
    #
    # loadMlflow
    #
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "MLFlow secret is not attached to the notebook"


def test_mlflow_init_exp(config, driver):
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '' or pytest.notebook.wait_for_output_of_the_current_cell() == "INFO: 'demoexp' does not exist. Creating a new experiment\n", "Mlflow error"
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Mlflow error"
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Mlflow error"

pattern = r"Elasticnet model\s+[(]alpha=(\d+\.\d+),\s+l1_ratio=(\d+\.\d+)[)]:\s+RMSE:\s+\d+\.\d+\s+MAE:\s+\d+\.\d+\s+R2:\s+\d+\.\d+(\s*)"

def test_mlflow_train(config, driver):
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    m = re.match(pattern, pytest.notebook.wait_for_output_of_the_current_cell())
    value = "0.500000"
    assert m is not None and m.group(1) == value and m.group(2) == value, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    error_output = pytest.notebook.is_there_an_error_in_notebook()
    assert not error_output, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    pytest.notebook.click_play()
    m = re.match(pattern, pytest.notebook.wait_for_output_of_the_current_cell())
    value = "0.200000"
    assert m is not None and m.group(1) == value and m.group(2) == value, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    pytest.notebook.click_play()
    value = "0.100000"
    m = re.match(pattern, pytest.notebook.wait_for_output_of_the_current_cell())
    assert m is not None and m.group(1) == value and m.group(2) == value, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"


def test_mlflow_train_the_best_model(config, driver):
    # time.sleep(10)
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    output = pytest.notebook.wait_for_output_of_the_current_cell()
    assert 'No training engine cluster attached' not in output, 'No training engine cluster attached'
    m = re.search(r"Training Cluster(\s*)ML Engine(\s*)(-*)(\s*)(-*)\s+(.+?)(\s+)python(\s*)", output)
    assert m.group(6) == config['training']['name'], "Train cluster name doesn't match"
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(""), "Mlflow error"
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    assert pytest.notebook.wait_output(""), "Mlflow error"
    pytest.notebook.click_play()
    output = pytest.notebook.wait_for_output_of_the_current_cell()
    assert re.match(r"<a .*</a>\s+Job Status:.*\s+" + pattern, pytest.notebook.wait_for_output_of_the_current_cell()) is not None, "Error while training the best model"
