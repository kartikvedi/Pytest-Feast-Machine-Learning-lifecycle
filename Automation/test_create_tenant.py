import time
import logging
import pytest

from core.platform_prepare import add_secrets
from core.pageobjects import TenantPageObject, AddUserPageObject

_log = logging.getLogger(__name__)


def test_login(config, driver):
    pytest.page = TenantPageObject(driver, url=config['url'] + '/bdswebui/k8s/tenants')
    pytest.page.do_login('admin', config['password'])


def is_needed_to_adopt_existing_ns(config):
    return 'adopt_existing' in config['tenant'] and config['tenant']['adopt_existing'] is True


def create_ns(name, exec_cmd_with_output_handler):
    expected_output = f'namespace/{name} created|configured|unchanged'
    assert exec_cmd_with_output_handler(f'kubectl create ns {name} --dry-run=client -o yaml | kubectl apply -f -',
                                        expected_output)[0] is True, 'Unable to create namespace for tenant'


def test_create_tenant(config, exec_cmd_with_output_handler):
    tenant_config = config['tenant']
    ns_name = tenant_config['namespace'] if 'namespace' in tenant_config else tenant_config['name']
    is_needed_to_create_ns = is_needed_to_adopt_existing_ns(config)
    if is_needed_to_create_ns:
        create_ns(ns_name, exec_cmd_with_output_handler)
    time.sleep(5)
    pytest.page.create_tenant(config['tenant']['name'], ns_name, 'Pytest auto created tenant', '10000',
                              ext_auth_role=config['tenant']['ext_auth_role'], ext_auth=config['tenant']['ext_auth'],
                              adopt_existing=is_needed_to_create_ns)

    # TODO: Add checker tenant status in progress class: #MuiTypography-root jss3964 blinking MuiTypography-body2
    time.sleep(30)  # Wait tenant initialized


def test_add_external_user(driver, config):
    # TODO: Check user exists
    page = AddUserPageObject(driver)
    page.open_url(config['url'] + '/bdswebui/createuser')
    page.set_external_user()
    page.set_input_field_by_id('name', config['tenant']['user_name'])
    page.click_button('Submit')


def test_assign_user_to_tenant(driver, config):
    pytest.page.open_url(config['url'] + '/bdswebui/k8s/tenants', 'Tenants')
    time.sleep(3)

    assert pytest.page.switch_to_tenant(config['tenant']['name']), 'Unable to switch to tenant'
    time.sleep(3)

    pytest.page.open_url(config['url'] + '/bdswebui/k8stenant/tenant-users')
    assert pytest.page.assign_user(config['tenant']['user_name'],
                                   config['tenant']['user_role']), 'Unable to assign user to tenant'


def test_add_mlflow_s3_secrets(config, exec_cmd_with_output_handler):
    tenant = config['tenant']
    name = tenant['namespace'] if 'namespace' in tenant else tenant['name']
    if tenant['add_secrets'] is True:

        assert add_secrets(exec_cmd_with_output_handler, name), 'Unable to add secrets to tenant'
    else:
        _log.info('Secrets skipped')
