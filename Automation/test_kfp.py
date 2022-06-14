import pytest
import re

import test_notebook


def test_open_kfp_example(config, driver):
    test_notebook.test_nb_login(config, driver)
    test_notebook.test_nb_open_example(config, driver)
    test_notebook.test_nb_restart_kernel(driver)
    test_notebook.test_nb_examples_init_vars(config, driver)

    test_notebook.pytest.notebook.open_url(test_notebook.pytest.notebook._url + '/hub/user-redirect/lab/tree/examples/kubeflow/kfp/Kubeflow_Utils_Example.ipynb')


def test_run_kfp_example(config, driver):
    test_notebook.pytest.notebook.click_all_play()
    test_notebook.pytest.notebook.confirm_dialog()
    test_notebook.wait(10)
    ask_for_auth = any(re.search('please enter your password',  s.text) for s in
               pytest.notebook.get_output_arr())
    if ask_for_auth:
        test_notebook.pytest.notebook.authorize_inside_nb(config["password"])
        test_notebook.wait(5)
    if re.search(r'https://', test_notebook.pytest.notebook._url):
        test_notebook.pytest.notebook.set_cert_inside_nb(config["login"])
        test_notebook.wait(5)
        assert any(re.search('The path to CA certification',  s.text) for s in
               pytest.notebook.get_output_arr()) is False, 'No certificate'
    test_notebook.wait(10)
    outputs = pytest.notebook.get_output_arr()
    assert any(re.search(r"'name':\s+'\[Demo\] XGBoost - Iterative model '",  s.text) for s in outputs), 'No pipelines output'
    assert any(re.search(r"'name':\s+'\[Demo\] TFX - Taxi tip prediction '",  s.text) for s in outputs), 'No pipelines output'
    assert any(re.search(r"'name':\s+'\[Tutorial\] Data passing in python components",  s.text) for s in outputs), 'No pipelines output'
    assert any(re.search(r"'This sample demonstrates iterative training '",  s.text) for s in outputs), 'No pipelines output'
    assert any(re.search(r"'Example pipeline that does classification with '",  s.text) for s in outputs), 'No pipelines output'
    assert any(re.search(r"'Shows how to pass data between python '",  s.text) for s in outputs), 'No pipelines output'
