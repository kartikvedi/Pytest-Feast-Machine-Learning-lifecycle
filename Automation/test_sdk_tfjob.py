import pytest
import re
from core.pageobjects import NotebookPageObject

import test_notebook
import pytest

def test_open_sdk_tf_example(config, driver):
    test_notebook.test_nb_login(config , driver)
    test_notebook.test_nb_open_example(config , driver)
    test_notebook.test_nb_restart_kernel(driver)
    test_notebook.test_nb_examples_init_vars(config , driver)
    test_notebook.test_nb_examples_kuberefresh(config, driver)
    pytest.notebook.open_url(pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/kubeflow/sdk/tf/tf-example.ipynb')

def test_imports(driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Import failed"
    
def test_env_vars(driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Set env vars for DOMAIN, NAMESPACE OR HOME failed"
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Set env vars for JOB_NAME failed"
    
def test_declare_tfjob(driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Declare TFJob object failed"

def test_create_client(driver):
    pytest.notebook.click_play()
    assert pytest.notebook.wait_for_output_of_the_current_cell() == '', "Can not create TFJob client"
    
def test_create_tfjob(driver):
    pytest.notebook.click_play()
    res = pytest.notebook.wait_for_output_of_the_current_cell()
    assert '"message":"tfjobs.kubeflow.org \\"sdk-tf-mnist\\" already exists"' not in res, "Job already exists"
    assert "'kind': 'TFJob'," in res, "Job creation failed"
    assert "'name': 'sdk-tf-mnist'," in res, "Job creation failed"
    assert "'image': 'gcr.io/kubeflow-ci/tf-mnist-with-summaries:1.0'," in res, "Job creation failed"
    assert "'name': 'tensorflow'," in res, "Job creation failed"
    
def test_is_job_succeeded(driver):
    pytest.notebook.click_play()
    res = pytest.notebook.wait_for_output_of_the_current_cell(10)
    assert res != 'True', "Job shouldn't be succeeded at this point"
    assert res == 'False', "check is_job_succeeded failed"
    
def test_wait_for_job(config, driver):
    pytest.notebook.click_play()
    pytest.notebook.click_play()
    res = pytest.notebook.wait_for_output_of_the_current_cell(config['notebook']['command_execution_max_timeout'])
    # assert re.search(r"NAME\s+STATE\s+TIME", res) is not None, "Job creation failed" # This output is not always present
    # assert re.search(r"sdk-tf-mnist\s+Created\s+\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", res) is not None, "Wait for job Created failed" # This output is not always present
    assert re.search(r"sdk-tf-mnist\s+Running\s+\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", res) is not None, "Wait for job Running failed"
    assert re.search(r"sdk-tf-mnist\s+Succeeded\s+\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", res) is not None , "Wait for job Succeeded failed"
    
def test_is_job_succeeded(driver):
    pytest.notebook.click_play(5)
    res = pytest.notebook.wait_for_output_of_the_current_cell()
    assert res != 'False', "Job should be succeeded at this point"
    assert res == 'True', "check is_job_succeeded failed"
    
def test_delet_job(driver):
    pytest.notebook.click_play()
    res = pytest.notebook.wait_for_output_of_the_current_cell()
    assert "'kind': 'Status'" in res, "Job deletion failed"
    assert "'status': 'Success'" in res, "Job deletion failed"
    assert "'name': 'sdk-tf-mnist'" in res, "Job deletion failed"
    assert "'group': 'kubeflow.org'" in res, "Job deletion failed"
    assert "'kind': 'tfjobs'" in res, "Job deletion failed"
    
