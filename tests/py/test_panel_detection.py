import pytest
import mock
from modules import InstallManager
from modules.cpanel import cPanelManager
from modules.plesk import PleskManager
from modules.da import DirectAdminManager


@pytest.mark.parametrize("mocked_content, expected", [
    ('cPanel', cPanelManager),
    ('Plesk', PleskManager),
    ('DirectAdmin', DirectAdminManager),
    ('Unknown', InstallManager)
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_panel_detection(mocked_content, expected):
    res = InstallManager.factory(mocked_content)
    assert res.__class__ == expected

managerlist = ['Unknown', 'DirectAdmin', 'Plesk', "ISPManager", "InterWorx"]
@pytest.fixture(params=managerlist)
def manager_instance(request):
    """
    Go through all the available panels (except cPanel)
    """
    with mock.patch("builtins.open", mock.mock_open(read_data='')):
        m = InstallManager.factory(request.param)
    return m

@pytest.mark.parametrize("mocked_content", [
    'mariadb104',
    'mariadb105',
    'mariadb103',
    'mysql57',
])
def test_for_supported_db_version(manager_instance, mocked_content):
    """
    This test checks that the tested method does not affect for any
    panels except cPanel
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.cpanel.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                        return_value=mocked_content):
            manager_instance.unsupported_db_version()
    exit_mock.assert_not_called()
