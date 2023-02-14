import json
import pytest
from unittest import mock
from pyfakefs.fake_filesystem_unittest import Patcher
import governor_package_limitting
import creates_individual_limits_vector_list
import subprocess
import yaml


#@pytest.fixture(scope='session', autouse=True)
#def dbctl_sync_mock():
#    with mock.patch('governor_package_limitting.dbctl_sync') as _fixture:
#        yield _fixture

@pytest.fixture
def fs():
    with Patcher() as patcher:
        patcher.fs.create_dir('/var/run')
        yield patcher.fs

empty_config = {"package_limits": {}, "individual_limits": {}}
broken_config = ""

cp_packages_mock = {'default': ['user0', 'user10', 'user11', 'user12', 'user13',
                                'user14', 'user15', 'user16', 'user17', 'user18',
                                'user19', 'user20', 'user21', 'user22', 'user3',
                                'user4', 'user5', 'user6', 'user7', 'user8', 'user9'],
                    'pack_1': ['user1'],
                    'pack_2': ['user2']
                   }

get_package_limit_mock_full = {'package_limits': {'pack_1': {'cpu': [0, 0, 0, 0],
                                                             'read': [0, 0, 0, 0],
                                                             'write': [0, 0, 0, 0]},
                                                  'pack_2': {'cpu': [0, 0, 0, 0],
                                                             'read': [0, 0, 0, 0],
                                                             'write': [0, 0, 0, 0]},
                                                  'default': {'cpu': [0, 0, 0, 0],
                                                              'read': [0, 0, 0, 0],
                                                              'write': [0, 0, 0, 0]}},
                               'individual_limits': {}
                              }

get_package_limit_mock_pack_1_only = {'pack_1': {'cpu': [0, 0, 0, 0],
                                                 'read': [0, 0, 0, 0],
                                                 'write': [0, 0, 0, 0]
                                                }
                                     }

config_content = {
    "package_limits": {
        'package1': {'cpu': [150, 100, 70, 50],
                     'read': [0, 0, 0, 0],
                     'write': [0, 0, 0, 0]
                    },
        'package2': {'cpu': [15, 10, 7, 5],
                     'read': [1048576, 2097152, 3145728, 4194304],
                     'write': [0, 0, 0, 0]
                    }
        },
    "individual_limits": {}
}

config_content_2 = {
    "package_limits": {
        'package1': {'cpu': [300, 200, 100, 50],
                     'read': [524288000, 419430400, 314572800, 209715200],
                     'write': [262144000, 157286400, 52428800, 5242880]
                    },
        'package2': {'cpu': [15, 10, 7, 5],
                     'read': [5242880, 1048576, 100000, 0],
                     'write': [0, 0, 0, 0]
                    }
    },
    "individual_limits": {
        "user1": {"cpu": [True] * 4,
                   "read": [True] * 4,
                   "write": [True] * 4
                 },
        "user2": {"cpu": [True] * 4,
                  "read": [True, True, True, False],
                  "write": [False] * 4
                 }
    }
}

dbctl_output = { "default": {"cpu": {"current": 400, "short": 380, "mid": 350, "long": 300},
                             "read": {"current": 953, "short": 791, "mid": 724, "long": 562},
                             "write": {"current": 953, "short": 791, "mid": 724, "long": 562}
                            },
                 "user1": {"cpu": {"current": 100, "short": 100, "mid": 100, "long": 100},
                           "read": {"current": 209715200, "short": 209715200, "mid": 209715200, "long": 209715200},
                           "write": {"current": 314572800, "short": 314572800, "mid": 314572800, "long": 314572800}
                          }
               }


@pytest.mark.parametrize("test_input, expected", [
    (
        ['package1', ['1,2,3'], ['10, 5'], None],
        {'package1': {'cpu': [1, 2, 3, 0], 'read': [10485760, 5242880, 0, 0], 'write': [0, 0, 0, 0]}}
    ),
    (
        ['package2', None, None, None],
        {'package2': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]}}
    )
])
@mock.patch("governor_package_limitting.os.path.exists",
            mock.MagicMock(return_value=True))
def test_set_package_limits(test_input, expected, fs):
    # For 'read' limits we set data as megabytes and get as bytes
    # (other formats are available in stdout only)
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(empty_config)
    )
    governor_package_limitting.fill_gpl_json(*test_input)
    cfg = governor_package_limitting.get_package_limit(test_input[0])
    assert cfg == expected


@pytest.mark.parametrize('test_input, expected_content', [
    (
        ['package1', None, ['50, 51200k, 52428800b, 50m'], None],
        {'package1': {'cpu': [150, 100, 70, 50], 'read': [52428800, 52428800, 52428800, 52428800], 'write': [0, 0, 0, 0]}}
    )
])
@mock.patch("governor_package_limitting.os.path.exists",
            mock.MagicMock(return_value=True))
def test_update_package_limit(test_input, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_content)
    )
    governor_package_limitting.fill_gpl_json(*test_input)
    cfg = governor_package_limitting.get_package_limit(test_input[0])
    assert cfg == expected_content


########################################################################################################################


expected_cfg = {
    "package_limits": {
        'package2': {'cpu': [15, 10, 7, 5],
                     'read': [1048576, 2097152, 3145728, 4194304],
                     'write': [0, 0, 0, 0]
                    }
        },
    "individual_limits": {}
}

@pytest.mark.parametrize("config_file_content, expected",
                         [(config_content, expected_cfg),])
@mock.patch("governor_package_limitting.os.path.exists",
            mock.MagicMock(return_value=True))
def test_delete_package_limits(config_file_content, expected, fs):
    fs.create_file(
        governor_package_limitting.PACKAGE_LIMIT_CONFIG,
        contents=json.dumps(config_file_content)
    )
    governor_package_limitting.delete_package_limit('package1')
    cfg = governor_package_limitting.get_package_limit()
    assert cfg == expected


########################################################################################################################


@pytest.mark.parametrize('config_file_content, expected_content', [
    (config_content, config_content),
    (broken_config, empty_config)
])
@mock.patch("governor_package_limitting.os.path.exists",
            mock.MagicMock(return_value=True))
def test_get_package_limits(config_file_content, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_file_content)
    )
    governor_package_limitting.ensure_json_presence()
    cfg = governor_package_limitting.get_package_limit()
    assert cfg == expected_content


@pytest.mark.parametrize('config_file_content, expected_content',
                         [(config_content, config_content)])
@mock.patch("governor_package_limitting.os.path.exists",
            mock.MagicMock(return_value=True))
def test_get_package_limit(config_file_content, expected_content, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_file_content)
    )
    cfg = governor_package_limitting.get_package_limit('package1')
    assert cfg == {'package1': expected_content['package_limits']['package1']}


#########################################################################################################################


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
def test_byte_size_convertor(test_value, from_format, to_format,
                             exptected_result):
    result = governor_package_limitting.byte_size_convertor(
        test_value, from_format, to_format
    )
    assert result == exptected_result


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


@pytest.mark.parametrize('test_input, exptected_result',
    [({'cpu': [10, 10, 10, 10], 'read': ['10485760b', '10240k', '10m', '10'],
       'write': [20971520, 20971520, 20971520, 20971520]
      },
      {'cpu': [10, 10, 10, 10], 'read': [10485760, 10485760, 10485760, 10485760],
       'write': [20971520, 20971520, 20971520, 20971520]
      }
     ),
    ]
)
def test_convert_io_rw_to_mb_if_bytes_provided(test_input, exptected_result):
    result = governor_package_limitting.convert_io_rw_to_bb(test_input)
    assert result == exptected_result


########################################################################################################################


@pytest.mark.parametrize('default_content, exptected_result',
    [(config_content,
      {'c_package1': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]},
       'c_package2': {'cpu': [0, 0, 0, 0], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]},
       'package1': {'cpu': [150, 100, 70, 50], 'read': [0, 0, 0, 0], 'write': [0, 0, 0, 0]},
       'package2': {'cpu': [15, 10, 7, 5], 'read': [1048576, 2097152, 3145728, 4194304], 'write': [0, 0, 0, 0]}
      }
     ),
    ]
)
@mock.patch("governor_package_limitting.admin_packages",
            mock.MagicMock(return_value=['c_package1', 'c_package2']))
def test_sync_with_panel(default_content, exptected_result, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_content)
    )
    governor_package_limitting.sync_with_panel()
    result = governor_package_limitting.get_package_limit()
    assert exptected_result == result['package_limits']


############################# VECTOR #############################


@pytest.mark.parametrize("test_input, expected",
    [(['user1', ['true,true,true,true'], ['false,false,false,false'], ['true,true,true,false']],
      {"user1": {"cpu": [True] * 4,
                 "read": [False] * 4,
                 "write": [True, True, True, False]
                }
      }
     ),
     (['user2', None, ['true,false,false,true'], None],
      {"user2": {"cpu": [False] * 4,
                 "read": [True, False, False, True],
                 "write": [False] * 4
                }
      }
     )
    ]
)
def test_set_individual(test_input, expected, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(empty_config)
    )
    governor_package_limitting.fill_gpl_json(*test_input, serialize=True,
                                             set_vector=True)
    cfg = governor_package_limitting.get_individual(test_input[0])

    assert cfg == expected


@pytest.mark.parametrize("expected, user",
    [({"user1": {"cpu": [True] * 4,
                 "read": [True] * 4,
                 "write": [True] * 4
                }
      },
      'user1'
     ),
     ({"user2": {"cpu": [True] * 4,
                 "read": [True, True, True, False],
                 "write": [False] * 4
                }
      },
      'user2'
     )
    ]
)
def test_get_individual(expected, user, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_content_2)
    )
    cfg = governor_package_limitting.get_individual(user)

    assert cfg == expected


@pytest.mark.parametrize("expected, user",
    [({"user1": {"cpu": [False] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user1'
     ),
     ({"user2": {"cpu": [False] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user2'
     )
    ]
)
@mock.patch("governor_package_limitting.run_dbctl_command",
            mock.MagicMock(return_value=None))
def test_reset_individual(expected, user, fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_content_2)
    )
    governor_package_limitting.reset_individual(user)
    cfg = governor_package_limitting.get_individual(user)

    assert cfg == expected


@pytest.mark.parametrize("expected, user, certain_limits_val",
    [({"user1": {"cpu": [False] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user1',
      'all'
     ),
     ({"user2": {"cpu": [False] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user2',
      'ALL'
     ),
     ({"user2": {"cpu": [False] * 4,
                 "read": [True, True, True, False],
                 "write": [False] * 4
                }
      },
      'user2',
      'mysql-cpu'
     ),
     ({"user2": {"cpu": [True] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user2',
      'mysql-io'
     ),
     ({"user2": {"cpu": [False] * 4,
                 "read": [False] * 4,
                 "write": [False] * 4
                }
      },
      'user2',
      'mysql-io,mysql-cpu'
     )
    ]
)
@mock.patch("governor_package_limitting.run_dbctl_command",
            mock.MagicMock(return_value=None))
@mock.patch("governor_package_limitting.get_dbctl_limits",
            mock.MagicMock(return_value=None))
@mock.patch("governor_package_limitting.return_the_individual_limits_to_dbctl",
            mock.MagicMock(return_value=None))
def test_reset_individual_with_certain_limits_var(expected, user, certain_limits_val, fs):
    # checks json changes only
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(config_content_2)
    )
    governor_package_limitting.reset_individual(user, certain_limits=certain_limits_val)
    cfg = governor_package_limitting.get_individual(user)

    assert cfg == expected


@pytest.mark.parametrize("package_limits, expected_out",
    [({"cpu": [200, 150, 100, 50], "read": [5000, -1, 300, 0],"write": [-1, 0, 0, 0]},
      ((200, 150, 100, 50), (5000, 0, 300, 0), (0, 0, 0, 0))
     ),
     ({"cpu": [-1, -1, -1, -1], "read": [-1, -1, 300, 0],"write": [-1, 500, 0, -1]},
      ((0, 0, 0, 0), (0, 0, 300, 0), (0, 500, 0, 0))
     )
    ]
)
def test_set_default_limits(package_limits, expected_out):
    out = governor_package_limitting.set_default_limit(package_limits)
    assert out == expected_out


#################################################################################################


dbctl_listjson_output = {
    "cpu": {"current": 400, "short": 300, "mid": -1, "long": 0},
    "read": {"current": 50000, "short": 40000, "mid": 30000, "long": -1},
    "write": {"current": -1, "short": 0, "mid": 3000, "long": -1}
}
limits_out = ((400, 300, -1, 0), (50000, 40000, 30000, -1), (-1, 0, 3000, -1))
@mock.patch("governor_package_limitting.trying_to_get_user_in_dbctl_list",
            mock.MagicMock(return_value=dbctl_listjson_output))
def test_get_dbctl_limits():
    with mock.patch("governor_package_limitting.subprocess.run") as output_mock:
        output_mock.return_value.stdout = json.dumps(dbctl_listjson_output)
        out = governor_package_limitting.get_dbctl_limits()
        assert out == limits_out


@pytest.mark.parametrize("vector, default_or_package_limit, individual_limits, res",
    [({'user1': {"cpu": [True] * 4, "read": [True] * 4, "write": [True] * 4}},
      ((400, 300, 200, 100), (500, 400, 300, 200), (550, 440, 330, 220)),
      ((220, 110, 55, 5), (330, 220, 110, 55), (220, 110, 44, 4)),
      ((220, 110, 55, 5), (330, 220, 110, 55), (220, 110, 44, 4))
     ),
     ({'user1': {"cpu": [False] * 4, "read": [False] * 4, "write": [False] * 4}},
      ((400, 300, 200, 100), (500, 400, 300, 200), (550, 440, 330, 220)),
      ((220, 110, 55, 5), (330, 220, 110, 55), (220, 110, 44, 4)),
      ((400, 300, 200, 100), (500, 400, 300, 200), (550, 440, 330, 220))
     ),
     ({'user1': {"cpu": [True] * 4, "read": [False] * 4, "write": [True, False, False, True]}},
      ((400, 300, 200, 100), (500, 400, 300, 200), (550, 440, 330, 220)),
      ((220, 110, 55, 5), (330, 220, 110, 55), (220, 110, 44, 4)),
      ((220, 110, 55, 5), (500, 400, 300, 200), (220, 440, 330, 4))
     )
    ]
)
def test_ensures_the_individual_limits_still_set(
    vector, default_or_package_limit, individual_limits, res):
    out = governor_package_limitting.ensures_the_individual_limits_still_set(
        vector, default_or_package_limit, individual_limits)
    assert out == res


limits = ((220, 110, 55, 5), (330, 220, 110, 55), (220, 110, 44, 4))
res = (('220,110,55,5'), ('330b,220b,110b,55b'), ('220b,110b,44b,4b'))
@mock.patch("governor_package_limitting.ensures_the_individual_limits_still_set",
            mock.MagicMock(return_value=limits))
@mock.patch("governor_package_limitting.set_default_limit",
            mock.MagicMock(return_value=(1,2,)))
@mock.patch("governor_package_limitting.get_dbctl_limits",
            mock.MagicMock(return_value=(1,2,)))
def test_prepare_limits():
    out = governor_package_limitting.prepare_limits(
        user='user1', package_limit={'a': 1}, individual_limit={'a': 1}
    )

    assert out == res


############################################################################################################


cfg_expected = {
    'individual_limits': {
        'user1': {'cpu': [False, False, False, False],
                  'read': [False, False, True, True],
                  'write': [True, False, False, True]
                 },
        'user2': {'cpu': [True, True, True, True],
                  'read': [True, True, True, True],
                  'write': [True, True, True, True]
                 },
        'user3': {'cpu': [False, False, False, False],
                  'read': [False, False, False, False],
                  'write': [False, False, False, False]
                 }
    },
    'package_limits': {}
}

dbctl_orig_list_raw = [
    ' user\tcpu(%)\tread( B/s)\twrite( B/s)',
    'default\t400/380/350/300\t1000000000/830000000/760000000/590000000\t1000000000/830000000/760000000/590000000',
    'user1\t0/0/-1/-1\t-1/0/232783872/116391936\t209715200/-1/0/104857600',
    'user2\t100/50/40/10\t465567744/349175808/232783872/116391936\t209715200/146800640/125829120/104857600',
    'user3\t-1/-1/-1/0\t-1/-1/-1/0\t-1/0/0/0',
    '']
@mock.patch("creates_individual_limits_vector_list.wait_for_governormysql_service_status",
            mock.MagicMock(return_value=True))
@mock.patch("creates_individual_limits_vector_list.get_dbctlorig_listraw",
            mock.MagicMock(return_value=dbctl_orig_list_raw))
def test_creates_individual_limits_vector_list(fs):
    fs.create_file(governor_package_limitting.PACKAGE_LIMIT_CONFIG,
                   contents=json.dumps(empty_config)
    )
    cfg_empty = governor_package_limitting.get_package_limit()
    creates_individual_limits_vector_list.fill_the_individual_limits()
    vector_list_out = governor_package_limitting.get_package_limit()

    assert cfg_empty == empty_config
    assert cfg_expected == vector_list_out


#########################################dbctl_sync########################################################################


run_dbctl_command_mock_3 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_full))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_3)
def test_dbctl_sync___action__set():
    governor_package_limitting.dbctl_sync(action='set')
    assert run_dbctl_command_mock_3.call_count == 3

run_dbctl_command_mock_1_1 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_pack_1_only))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_1)
def test_dbctl_sync___package_opt_action__set():
    governor_package_limitting.dbctl_sync(action='set', package='pack_1')
    assert run_dbctl_command_mock_1_1.call_count == 1

run_dbctl_command_mock_1_2 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_full))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_2)
def test_dbctl_sync___user_opt_action__set():
    governor_package_limitting.dbctl_sync(action='set', user='user10')
    assert run_dbctl_command_mock_1_2.call_count == 1

run_dbctl_command_mock_1_3 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_pack_1_only))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_3)
def test_dbctl_sync___user_and_package_opt_action__set():
    governor_package_limitting.dbctl_sync(action='set', package='pack_1', user='user1')
    assert run_dbctl_command_mock_1_3.call_count == 1

run_dbctl_command_mock_1_4 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_pack_1_only))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_4)
def test_dbctl_sync___user_is_not_contained_in_the_package():
    governor_package_limitting.dbctl_sync(action='set', package='pack_1', user='user2')
    assert run_dbctl_command_mock_1_4.call_count == 0

run_dbctl_command_mock_1_5 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=None))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_5)
def test_dbctl_sync___nonexistent_package__set():
    governor_package_limitting.dbctl_sync(action='set', package='pack_111')
    assert run_dbctl_command_mock_1_5.call_count == 0

run_dbctl_command_mock_1_6 = mock.MagicMock()
@mock.patch("governor_package_limitting.cp_packages",
            mock.MagicMock(return_value=cp_packages_mock))
@mock.patch("governor_package_limitting.get_package_limit",
            mock.MagicMock(return_value=get_package_limit_mock_full))
@mock.patch("governor_package_limitting.run_dbctl_command",
            run_dbctl_command_mock_1_6)
def test_dbctl_sync___nonexistent_user__set():
    governor_package_limitting.dbctl_sync(action='set', user='user100')
    assert run_dbctl_command_mock_1_6.call_count == 0
