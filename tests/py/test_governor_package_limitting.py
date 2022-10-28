import pytest
from unittest import mock
from pyfakefs.fake_filesystem_unittest import Patcher
import governor_package_limitting
import subprocess
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

config_content = """
package1:
  cpu: [150, 100, 70, 50]
  read: [0, 0, 0, 0]
  write: [0, 0, 0, 0]
package2:
  cpu: [15, 10, 7, 5]
  read: [1, 2, 3, 4]
  write: [0, 0, 0, 0]
"""


@pytest.mark.parametrize("test_input, expected", [
    (
        ['package1', ['1,2,3'], None, None],
        {'package1': {'cpu': [1, 2, 3, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]}}
    ),
    (
        ['rootруспакет', None, None, None],
        {'rootруспакет': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]}}
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



@pytest.mark.parametrize('test_input, expected_content', [
    (
        ['package1', None, ['50, 50, 50, 50'], None],
        {'package1': {'cpu': [150, 100, 70, 50], 'read': [50, 50, 50, 50], 'write': [0, 0, 0, 0]}}
    )
])
@mock.patch("governor_package_limitting.os.path.exists", mock.MagicMock(return_value=True))
def test_update_package_limit(test_input, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_content)
    governor_package_limitting.set_package_limits(*test_input)
    cfg = governor_package_limitting.get_package_limit(test_input[0])
    assert cfg == expected_content

########################################################################################################################


expected_cfg = {
    'package2': {
        'cpu': [15, 10, 7, 5],
        'read': [1, 2, 3, 4],
        'write': [0, 0, 0, 0]
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


########################################################################################################################


expected_cfg = {
    'package1': {
        'cpu': [150, 100, 70, 50],
        'read': [0, 0, 0, 0],
        'write': [0, 0, 0, 0]
    },
    'package2': {
        'cpu': [15, 10, 7, 5],
        'read': [1, 2, 3, 4],
        'write': [0, 0, 0, 0]
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
            'DEFAULT': {'cpu': [0, 150, 320, 0], 'read': [0, 20, 30, 40], 'write': [200, 200, 200, 200]},
            'PACK1': {'cpu': [111, 294, 0, 0], 'read': [0, 258, 0, 900], 'write': [100, 100, 100, 100]}
         },
        ('111,294,320,100', '200,258,30,900', '100,100,100,100')
    ),
    (
        {
            'DEFAULT': {'cpu': [927, 927, 927, 927], 'read': [927, 0, 927, 927], 'write': [0, 927, 927, 927]},
            'PACK1': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 100]}
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
def test_byte_size_convertor(test_value, from_format, to_format, exptected_result):
    result = governor_package_limitting.byte_size_convertor(test_value, from_format, to_format)
    assert result == exptected_result


@pytest.mark.parametrize(
    "default_config_content, expected_result", [
        (
            None,
            {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]}
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


########################################################################################################################

@pytest.mark.parametrize(
    'test_input, expected_result', [
        (['1,2,3,4'], ['1', '2', '3', '4']),
        (['10,20'], ['10', '20', 0, 0]),
    ]
)
def test_limits_serializer(test_input, expected_result):
    result = governor_package_limitting.limits_serializer(test_input)
    assert result == expected_result


@pytest.mark.parametrize(
    'test_input, expected_raise', [
        (['1,2,3,4,5'], SystemExit),
    ]
)
def test_limits_serializer_with_exception(test_input, expected_raise):
    with pytest.raises(expected_raise):
        governor_package_limitting.limits_serializer(test_input)


#########################################################################################################################

@pytest.mark.parametrize(
    'test_input, exptected_result', [
        (
            {'cpu': [10, 10, 10, 10], 'read': ['10485760b', '10485760b', '10485760b', '10485760b'], 'write': [20, 20, 20, 20]},
            {'cpu': [10, 10, 10, 10], 'read': [10, 10, 10, 10], 'write': [20, 20, 20, 20]}
        ),
    ]
)
def test_convert_io_rw_to_mb_if_bytes_provided(test_input, exptected_result):
    result = governor_package_limitting.convert_io_rw_to_mb_if_bytes_provided(test_input)
    assert result == exptected_result

########################################################################################################################


@pytest.mark.parametrize(
    'default_content, exptected_result', [
        (
            config_content, 
             {
                'c_package1': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]},
                'c_package2': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]}, 
                'package1': {'cpu': [150, 100, 70, 50], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]},
                'package2': {'cpu': [15, 10, 7, 5], 'read': [1, 2, 3, 4], 'write': [0, 0, 0, 0]}
                }
        ),
    ]
)
@mock.patch("governor_package_limitting.admin_packages", mock.MagicMock(return_value=['c_package1', 'c_package2']))
def test_sync_with_panel(default_content, exptected_result, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG, contents=config_content)
    governor_package_limitting.sync_with_panel()
    result = governor_package_limitting.get_package_limit()
    print('result ->' ,result)
    assert exptected_result == result