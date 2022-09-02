import pytest
from unittest import mock
from pyfakefs.fake_filesystem_unittest import Patcher
import governor_package_limitting

package1 = ['package1', ['1,2,3'], None, None]
expected_cfg = {'cpu': [1, 2, 3, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, -1]}


@pytest.fixture(scope='session', autouse=True)
def dbctl_sync_mock():
    with mock.patch('governor_package_limitting.dbctl_sync') as _fixture:
        yield _fixture


@pytest.mark.parametrize("test_input, expected", [
    (package1, expected_cfg)
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_set_package_limits(test_input, expected):
    with Patcher() as patcher:
        patcher.fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG)
        try:
            governor_package_limitting.set_package_limits(*test_input)
        except SystemExit as sysexit:
            assert sysexit.code == 0
        cfg = governor_package_limitting.get_package_limit('package1')
        assert cfg == expected

########################################################################################################################


config_content = """
package1:
  cpu: [150, 100, 70, 50]
  read: [-1, -1, -1, -1]
  write: [-1, -1, -1, -1]
package2:
  cpu: [15, 10, 7, 5]
  read: [1, 2, 3, 4]
  write: [-1, -1, -1, -1]
"""

expected_cfg = {
    'package2': {
        'cpu': [15, 10, 7, 5],
        'read': [1, 2, 3, 4],
        'write': [-1, -1, -1, -1]
    }
}


########################################################################################################################


@pytest.mark.parametrize("config_file_content, expected", [
    (config_content, expected_cfg),
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_delete_package_limits(config_file_content, expected):
    with Patcher() as patcher:
        patcher.fs.create_file(
            governor_package_limitting.PACKAGE_LIMIT_CONFIG,
            contents=config_file_content
        )
        governor_package_limitting.delete_package_limit('package1')
        cfg = governor_package_limitting.get_package_limit()
        assert cfg == expected


########################################################################################################################


config_content = """
package1:
  cpu: [150, 100, 70, 50]
  read: [-1, -1, -1, -1]
  write: [-1, -1, -1, -1]
package2:
  cpu: [15, 10, 7, 5]
  read: [1, 2, 3, 4]
  write: [-1, -1, -1, -1]
"""

expected_cfg = {
    'package1': {
        'cpu': [150, 100, 70, 50],
        'read': [-1, -1, -1, -1],
        'write': [-1, -1, -1, -1]
    },
    'package2': {
        'cpu': [15, 10, 7, 5],
        'read': [1, 2, 3, 4],
        'write': [-1, -1, -1, -1]
    }
}


@pytest.mark.parametrize('config_file_content, expected_content', [
    (config_content, expected_cfg)
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_get_package_limits(config_file_content, expected_content):
    with Patcher() as patcher:
        patcher.fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_file_content)
        cfg = governor_package_limitting.get_package_limit()
        assert cfg == expected_content
