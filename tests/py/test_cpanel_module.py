import pytest
import mock
import sys
sys.path.append('../../install')
from modules import cpanel


@pytest.mark.parametrize("mocked_content, expected", [
    ('11.78.0.17', 78),
    ('11.72.0.4', 72)
])
def test_get_panel_version(mocked_content, expected):
    with mock.patch("__builtin__.open", mock.mock_open(read_data=mocked_content)):
        assert cpanel.cPanelManager('').get_panel_version() == expected
