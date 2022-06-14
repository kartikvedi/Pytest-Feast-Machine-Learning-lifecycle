import pytest
from core.pageobjects import LoginPageObject, NotebookPageObject
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import test_notebook
import re


def test_open_mlflow_example(config, driver):
    test_notebook.test_nb_login(config, driver)

    test_notebook.pytest.notebook.open_url(test_notebook.pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/mlflow/mlflow_example.ipynb')
    test_notebook.test_nb_restart_kernel(driver)


def test_mlflow_example_init_vars(config, driver):
    # test_notebook.pytest.notebook.change_cell(1, 'PASSWORD = "' + config["password"] + '"')
    pytest.notebook.replace_line_in_cell_after_header(f"PASSWORD = '{config['password']}'",
                                                      'Set-your-password-(mandatory)')
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    btn_play.click()


def test_mlflow_kuberefresh(config, driver):
    #
    # KubeRefresh
    #
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == 'kubeconfig set for user {0}\n'.format(
        config['login']), 'Unable to set Kubeflow section variables'


def test_mlflow_load(config, driver):
    #
    # loadMlflow
    #
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == 'Backend configured\n', "MLFlow secret is not attached to the notebook"


def test_mlflow_init_exp(config, driver):
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '' or pytest.notebook.wait_for_output_of_the_current_cell() == "INFO: 'demoexp' does not exist. Creating a new experiment\n", "Mlflow error"
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Mlflow error"
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Mlflow error"


def test_mlflow_train(config, driver):
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    btn_play.click()
    assert re.match(
        r"Elasticnet model [(]alpha=\d+\.\d+, l1_ratio=\d+\.\d+[)]:\n  RMSE: \d+\.\d+\n  MAE: \d+\.\d+\n  R2: \d+\.\d+(\n*)",
        pytest.notebook.wait_for_output_of_the_current_cell()) is not None, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    btn_play.click()
    assert re.match(
        r"Elasticnet model [(]alpha=\d+\.\d+, l1_ratio=\d+\.\d+[)]:\n  RMSE: \d+\.\d+\n  MAE: \d+\.\d+\n  R2: \d+\.\d+(\n*)",
        pytest.notebook.wait_for_output_of_the_current_cell()) is not None, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    btn_play.click()
    assert re.match(
        r"Elasticnet model [(]alpha=\d+\.\d+, l1_ratio=\d+\.\d+[)]:\n  RMSE: \d+\.\d+\n  MAE: \d+\.\d+\n  R2: \d+\.\d+(\n*)",
        pytest.notebook.wait_for_output_of_the_current_cell()) is not None, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"


def test_mlflow_train_the_best_model(config, driver):
    btn_play = pytest.notebook.buttons[5]
    btn_play.click()
    btn_play.click()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == 'Training Cluster        ML Engine\n----------------------  -----------\ntrainingengineinstance  python\n', "Train cluster name should be 'trainingengineinstance'"
    btn_play.click()
    btn_play.click()
    assert pytest.notebook.wait_output(""), "Mlflow error"
    btn_play.click()
    btn_play.click()
    assert pytest.notebook.wait_output(""), "Mlflow error"
    btn_play.click()
    output = pytest.notebook.wait_for_output_of_the_current_cell()
    assert output.startswith("<a ") and output.endswith("</a>\n"), "MLFlow error"
    assert not pytest.notebook.is_there_an_error_in_notebook(), "Train cluster name should be 'trainingengineinstance'"
    btn_play.click()
    assert re.match(
        r"Job Status: Finished\nElasticnet model [(]alpha=\d+\.\d+, l1_ratio=\d+\.\d+[)]:\n  RMSE: \d+\.\d+\n  MAE: \d+\.\d+\n  R2: \d+\.\d+(\n*)Job Status: Finished\nElasticnet model [(]alpha=\d+\.\d+, l1_ratio=\d+\.\d+[)]:\n  RMSE: \d+\.\d+\n  MAE: \d+\.\d+\n  R2: \d+\.\d+(\n*)",
        pytest.notebook.wait_for_output_of_the_current_cell()) is not None, "Either train cluster in not connected to the notebook or mlflow bucket does not exist in minio"
