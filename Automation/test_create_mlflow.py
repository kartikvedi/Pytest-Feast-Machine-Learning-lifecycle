import logging
import pytest

from core.pobj_applications import ApplicationsPageObject
from core.pobj_minio import MinioPageObject

_log = logging.getLogger(__name__)


def test_login(config, driver):
    pytest.page = ApplicationsPageObject(driver, url=config['url'] + '/bdswebui/k8stenant/applications/#kubedirector')
    pytest.page.do_login(config['login'], config['password'])

def test_create_mlflow(config, driver):
    '''
    Create MLFlow application
    :param config:
    :param driver:
    :return:
    '''
    app_conf = config['mlflow']
    app_name = app_conf['name']
    assert pytest.page.click_on_app('mlflow') is True, 'Unable to find application'
    assert pytest.page.submit_app_form(app_name) is True, 'Unable to fill application form'


def test_verify_mlflow(config, driver):
    #
    # Common configs
    #
    app_conf = config['mlflow']
    login = config['login']
    password = config['password']
    login_timeout = config['login_timeout_sec']

    #
    # Training configs
    #
    app_name = app_conf['name']
    creation_time_limit_seconds = app_conf['creation_max_timeout_seconds']

    #
    # Loop inside and check status
    #
    assert pytest.page.wait_creation_status_table(app_name, login, password, creation_time_limit_seconds,
                                                  login_timeout) is True, 'Unable to finish creation of mlflow application'


def test_add_bucket_to_minio(config, driver):
    mlflow = config['mlflow']
    bucket_name = mlflow['minio_bucket_name'] if 'minio_bucket_name' in mlflow else 'mlflow'
    minio_s3_bucket_url = pytest.page.get_app_url(mlflow['name'])

    minio = MinioPageObject(driver, url=minio_s3_bucket_url)
    assert minio.do_login(config['admin_login'], config['admin_password']) is True, 'Unable to login into Minio'
    if not minio.verify_bucket_exists(bucket_name):
        assert minio.create_bucket(bucket_name) is True, 'Unable to create bucket in Minio'
    assert minio.verify_bucket_exists(bucket_name) is True, 'Bucket not present on UI'
