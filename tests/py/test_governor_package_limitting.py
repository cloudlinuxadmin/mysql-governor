import pytest
from unittest import mock
from pyfakefs.fake_filesystem_unittest import Patcher
import governor_package_limitting
import subprocess
import utilities
import yaml


@pytest.fixture(scope='session', autouse=True)
def dbctl_sync_mock():
    with mock.patch('governor_package_limitting.dbctl_sync') as _fixture:
        yield _fixture

@pytest.fixture
def fs():
    with Patcher() as patcher:
        patcher.fs.create_dir('/var/run')
        yield patcher.fs


@pytest.mark.parametrize("test_input, expected", [
    (
        ['package1', ['1,2,3'], None, None],
        {'package1': {'cpu': [1, 2, 3, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, -1]}}
    ),
    (
        ['rootруспакет', None, None, None],
        {'rootруспакет': {'cpu': [-1, -1, -1, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, -1]}}
    )
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_set_package_limits(test_input, expected, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG)

    try:
        governor_package_limitting.set_package_limits(*test_input)
    except SystemExit as sysexit:
        assert sysexit.code == 0
    cfg = governor_package_limitting.get_package_limit(test_input[0])
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


@pytest.mark.parametrize("config_file_content, expected", [
    (config_content, expected_cfg),
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_delete_package_limits(config_file_content, expected, fs):
    fs.create_file(
        governor_package_limitting.PACKAGE_LIMIT_CONFIG,
        contents=config_file_content
    )
    governor_package_limitting.delete_package_limit('package1')
    cfg = governor_package_limitting.get_package_limit()
    assert cfg == expected


# ########################################################################################################################


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
def test_get_package_limits(config_file_content, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_file_content)
    cfg = governor_package_limitting.get_package_limit()
    assert cfg == expected_content


@pytest.mark.parametrize('config_file_content, expected_content', [
    (config_content, expected_cfg)
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_get_package_limit(config_file_content, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_file_content)
    cfg = governor_package_limitting.get_package_limit('package1')
    assert cfg == {'package1': expected_content['package1']}

#########################################################################################################################


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


@pytest.mark.parametrize(
    "test_value, from_format, to_format, exptected_result", [
        (10, 'mb', 'bb', 10485760),
        (10, 'mb', 'kb', 10240),
        (10, 'mb', 'mb', 10),
        (52428800, 'bb', 'mb', 50),
        (52428800, 'bb', 'kb', 51200),
        (52428800, 'bb', 'bb', 52428800),
        (39936, 'kb', 'mb', 39),
        (39936, 'kb', 'bb', 40894464)
    ]
)
def test_format_calc(test_value, from_format, to_format, exptected_result):
    result = governor_package_limitting.format_calc(test_value, from_format, to_format)
    assert result == exptected_result


@pytest.mark.parametrize(
    "default_config_content, expected_result", [
        (
            None,
            {'cpu': [-1, -1, -1, -1], 'read': [-1, -1, -1, -1], 'write': [-1, -1, -1, -1]}
        ),
        (
            b"{'default': {'cpu': [1,1,1,1], 'read': [2,2,2,2], 'write': [3,3,3,3]}}",
            {'cpu': [1, 1, 1, 1], 'read': [2, 2, 2, 2], 'write': [3, 3, 3, 3]}
        ),
    ]
)
def test_check_and_set_default_value(default_config_content, expected_result, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=default_config_content)
    governor_package_limitting.check_and_set_default_value()
    assert governor_package_limitting.DEFAULT_PACKAGE_LIMITS == expected_result
