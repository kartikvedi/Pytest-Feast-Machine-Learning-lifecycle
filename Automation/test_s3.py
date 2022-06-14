import pytest
import re
from core.pageobjects import NotebookPageObject
from selenium.webdriver.support.ui import WebDriverWait

import test_notebook

def test_open_minio_example(config, driver):
    test_notebook.test_nb_login(config , driver)
    test_notebook.test_nb_open_example(config , driver)
    test_notebook.test_nb_restart_kernel(driver)

def test_run_minio_example(config , driver): 
    test_notebook.test_nb_examples_init_vars(config , driver)
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.select_cell_after_header("s3-upload/download-(AWS)")
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.select_cell_after_header("s3-upload/download-(MinIO)")
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.click_play()
    test_notebook.pytest.notebook.click_play()
    test_notebook.wait(10)
    assert any(re.search('MinIO endpoint:' ,  s.text) for s in
               pytest.notebook.get_output_arr()) , 'No minio endpoint'
    assert any(re.search('File uploaded to s3' ,  s.text) for s in
               pytest.notebook.get_output_arr()) , 'Cannot upload to s3'
    assert any(re.search('File downloaded from s3' ,  s.text) for s in
               pytest.notebook.get_output_arr()) , 'Cannot download from s3'
