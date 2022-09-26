import pytest
from unittest import mock
from pyfakefs.fake_filesystem_unittest import Patcher
import governor_package_limitting

package1 = ['package1', ['1,2,3'], None, None]
expected_cfg = {'package1': {'cpu': [1, 2, 3, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, -1]}}


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


@pytest.mark.parametrize('config_file_content, expected_content', [
    (config_content, expected_cfg)
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_get_package_limit(config_file_content, expected_content):
    with Patcher() as patcher:
        patcher.fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_file_content)
        cfg = governor_package_limitting.get_package_limit('package1')
        assert cfg == {'package1': expected_content['package1']}

########################################################################################################################


dbctl_output = 'user1    100/100/100/100      200/200/200/200       300/300/300/300   \n'


@pytest.mark.parametrize("test_input, expected_limit", [
    (
        {
            'DEFAULT': {'cpu': [-1, 150, 320, -1], 'read': [-1, 20, 30, 40], 'write': [200, 200, 200, 200]},
            'PACK1': {'cpu': [111, 294, -1, -1], 'read': [-1, 258, -1, 900], 'write': [100, 100, 100, 100]}
         },
        ('111,294,320,100', '200,258,30,900', '100,100,100,100')
    ),
    (
        {
            'DEFAULT': {'cpu': [927, 927, 927, 927], 'read': [927, -1, 927, 927], 'write': [-1, 927, 927, 927]},
            'PACK1': {'cpu': [-1, -1, -1, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, 100]}
        },
        ('927,927,927,927', '927,200,927,927', '300,927,927,100')
    ),
])
def test_prepare_limits(test_input, expected_limit):
    with mock.patch("governor_package_limitting.DEFAULT_PACKAGE_LIMITS", test_input.get('DEFAULT')),\
            mock.patch("governor_package_limitting.subprocess.run") as output_mock:
        output_mock.return_value.stdout = dbctl_output
        received_limit = governor_package_limitting.prepare_limits('user1', test_input.get('PACK1'))
        assert received_limit == expected_limit