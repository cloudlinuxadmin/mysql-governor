import pytest
import mock
from modules import cpanel


@pytest.mark.parametrize("mocked_content, expected", [
    ('11.78.0.17', 78),
    ('11.72.0.4', 72)
])
def test_get_panel_version(mocked_content, expected):
    with mock.patch("builtins.open", mock.mock_open(read_data=mocked_content)):
        assert cpanel.cPanelManager('').get_panel_version() == expected


@pytest.mark.parametrize("original, expected", [
    ('', None),
    ('invalid message', None),
    (
    '\nCpanel::Exception::Database::CpuserNotInMap/(XID fh46zu) The cPanel user “user_1” does not exist in the database map.\n at /usr/local/cpanel/Cpanel/DB/Map.pm line 223, <FILENAME> line 8.\n\tCpanel::DB::Map::_initialize_data(Cpanel::DB::Map=HASH(0x2944408)) called at /usr/local/cpanel/Cpanel/DB/Map.pm line 119\n\tCpanel::DB::Map::new("Cpanel::DB::Map", HASH(0x295d4b8)) called at /usr/local/cpanel/Cpanel/DB.pm line 49\n\tCpanel::DB::get_map(HASH(0x29711b0)) called at /usr/share/lve/dbgovernor/scripts/dbgovernor_map line 115\n\tmain::get_map_list_() called at /usr/share/lve/dbgovernor/scripts/dbgovernor_map line 66\n',
    'user_1'),
    (
    '\nCpanel::Exception/(XID w8xz59) The system failed to load and to parse the file “/var/cpanel/databases/user.json” because of an error: (XID wda8ub) The system failed to parse the JSON stream data \xe2\x80\x9c{"MYSQL":{"dbs":{"*":"192.168.245.46"},"noprefix":{},"dbusers":{},"server":"192.168.245.46","owner":"user"},"version":1\n\xe2\x80\x9d for the caller \xe2\x80\x9c(eval)\xe2\x80\x9d because of an error: , or } expected while parsing object/hash, at character offset 120 (before "(end of string)") at /usr/local/cpanel/Cpanel/JSON.pm line 123, <FILENAME> line 8.\n\n at /usr/local/cpanel/Cpanel/Transaction/File/BaseReader.pm line 61, <FILENAME> line 8.\n\tCpanel::Transaction::File::BaseReader::_init_data_with_catch(Cpanel::Transaction::File::JSON=HASH(0x1c39120), "sysopen_flags", 0, "permissions", 416, "path", "/var/cpanel/databases/user.json", "ownership", ...) called at /usr/local/cpanel/Cpanel/Transaction/File/BaseReader.pm line 74\n\tCpanel::Transaction::File::BaseReader::_get_data(Cpanel::Transaction::File::JSON=HASH(0x1c39120)) called at /usr/local/cpanel/Cpanel/DB/Map.pm line 240\n\tCpanel::DB::Map::_initialize_data(Cpanel::DB::Map=HASH(0x1c38f40)) called at /usr/local/cpanel/Cpanel/DB/Map.pm line 119\n\tCpanel::DB::Map::new("Cpanel::DB::Map", HASH(0x1c38e20)) called at /usr/local/cpanel/Cpanel/DB.pm line 49\n\tCpanel::DB::get_map(HASH(0x1c42b08)) called at /usr/share/lve/dbgovernor/scripts/dbgovernor_map line 115\n\tmain::get_map_list_() called at /usr/share/lve/dbgovernor/scripts/dbgovernor_map line 66\n',
    None)
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_retrieve_username(original, expected):
    assert cpanel.cPanelManager('').retrieve_username(original) == expected


@pytest.mark.parametrize("exception, expected_msg", [
    ('Error!!!', 'Error!!!'),
    ("\nCpanel::Exception::Database::CpuserNotInMap/(XID fh46zu) The cPanel user “user1” does not exist in the database map.\n at /usr/local/cpanel/Cpanel/DB/Map.pm line 223",
     'Try to perform the following command: /scripts/rebuild_dbmap user1')
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_update_user_map_exceptions(exception, expected_msg, capfd):
    """
    Check exitcode along with thrown message in case of RuntimeError
    """
    with mock.patch('modules.cpanel.cPanelManager._script_subprocess', side_effect=RuntimeError(exception)):
        with pytest.raises(SystemExit):
            assert cpanel.cPanelManager('').update_user_map_file()
        out, err = capfd.readouterr()
        assert expected_msg in out


@pytest.mark.parametrize("mocked_content", [
    'mariadb104',
    'mariadb105',
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_for_unsupported_db_version(mocked_content):
    """
    This test is to check the response of the tested method to an unsupported
    version of the database (expected "exit 1")
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.cpanel.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                        return_value=mocked_content):
            cpanel.cPanelManager('').unsupported_db_version()
    exit_mock.assert_called_once_with(1)


@pytest.mark.parametrize("mocked_content", [
    'mariadb104',
    'mariadb105',
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_for_unsupported_db_version_with_force(mocked_content):
    """
    This test is to check the response of the tested method to an unsupported
    version of the database (do nothing cause "force" key is passed)
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.cpanel.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                        return_value=mocked_content):
            cpanel.cPanelManager('').unsupported_db_version(force=True)
    exit_mock.assert_not_called()


@pytest.mark.parametrize("mocked_content", [
    'mariadb103',
    'mysql57',
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_for_supported_db_version(mocked_content):
    """
    This test is to check the response of the tested method to a supported
    version of the database (do nothing)
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.cpanel.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                        return_value=mocked_content):
            cpanel.cPanelManager('').unsupported_db_version()
    exit_mock.assert_not_called()
