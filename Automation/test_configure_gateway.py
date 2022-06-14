import logging
import pytest

from core.pageobjects import GWPageObject

_log = logging.getLogger(__name__)

def test_gateway_login(config, driver, host_passwd):
    pytest.platform = GWPageObject(driver=driver, url=config['url'] + '/bdswebui/gatewaylb',
                                   admin_login=config['admin_login'], admin_password=config['admin_password'], gw_ip=config['gateway_lb_ip'],
                                   gw_hostname=config['gateway_lb_hostname'], host_passwd=host_passwd)
    pl = pytest.platform
    pl.trigger('ev_http_connect')
    assert pl.is_st_http_ready()

    pl.trigger('ev_check_initial')
    if pl.is_st_initial():
        pl.trigger('ev_initial')


def test_gateway_enter_lockdown_configure(config, driver):
    pl = pytest.platform

    pl.trigger('ev_logging_in')
    assert pl.is_st_do_auth()

    _log.info('trigger ev_check_gw')
    pl.trigger('ev_check_gw')
    _log.info('trigger ev_check_gw done')
    if not pl.is_st_gw_ready():
        _log.info('gw is not ready')
        _log.info('trigger ev_check_locked')
        pl.trigger('ev_check_locked')
        _log.info('trigger ev_check_locked done')
        if not pl.is_st_locked_down():
            _log.info('platform is not locked')

            _log.info('trigger ev_lockdown')
            pl.trigger('ev_lockdown')
            _log.info('trigger ev_lockdown done')

        _log.info('asserting is st locked down')
        assert pl.is_st_locked_down()
        _log.info('st is locked down')

        _log.info('trigger ev_configure_gw')
        pl.trigger('ev_configure_gw')
        _log.info('trigger ev_configure_gw done')

        _log.info('trigger ev_check_gw')
        pl.trigger('ev_check_gw')
        _log.info('trigger ev_check_gw done')

    _log.info('asserting is_st_gw_ready')
    assert pl.is_st_gw_ready()
    _log.info('is_st_gw_ready is done')


def test_gateway_site_exit_lockdown():
    _log.info('test test_platform_site_lockdown')
    pl = pytest.platform

    _log.info('trigger ev_check_locked')
    pl.trigger('ev_check_locked')

    _log.info('check st_locked_down')
    if pl.is_st_locked_down():
        _log.info('is_st_locked_down - true')
        pl.trigger('ev_exit_lockdown')
        _log.info('assert is_st_gw_ready')
        assert pl.is_st_gw_ready
        _log.info('assert is_st_gw_ready - true')
    else:
        _log.info('is_st_locked_down - false')
        assert not pl.is_st_locked_down(), 'Transition ERROR: Site should be unlocked'
        _log.info('assert not pl.is_st_locked_down passed')
    _log.info('end test test_platform_site_lockdown')
