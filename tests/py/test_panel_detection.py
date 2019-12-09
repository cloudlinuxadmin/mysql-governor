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
@mock.patch("__builtin__.open", mock.mock_open(read_data=''))
def test_panel_detection(mocked_content, expected):
    res = InstallManager.factory(mocked_content)
    assert res.__class__ == expected
