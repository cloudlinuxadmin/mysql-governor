import pytest
import mock
from modules import InstallManager


@pytest.mark.parametrize("mocked_content, expected", [
    (6, ["mysql.x86_64", "mysql-server.x86_64", "mysql-libs.x86_64", "mysql-devel.x86_64", "mysql-bench.x86_64", "libaio.x86_64"]),
    (7, ["mariadb.x86_64", "mariadb-server.x86_64", "mariadb-devel.x86_64", "mariadb-libs.x86_64", "mariadb-bench.x86_64", "libaio.x86_64"]),
    (8, ["mysql.x86_64", "mysql-server.x86_64", "mysql-libs.x86_64", "mysql-devel.x86_64", "libaio.x86_64"]),
])
@mock.patch("modules.base.exec_command", mock.MagicMock(return_value=''))
@mock.patch("modules.base.exec_command_out", mock.MagicMock())
@mock.patch("modules.base.download_packages", mock.MagicMock(return_value=True))
@mock.patch("modules.base.cl8_module_enable", mock.MagicMock())
@mock.patch("modules.base.os.uname", mock.MagicMock(return_value=('', 'x86_64')))
@mock.patch("modules.base.urllib.request.urlopen", mock.MagicMock())
@mock.patch("modules.base.write_file", mock.MagicMock())
def test_load_new_packages_auto(mocked_content, expected):
    with mock.patch("modules.base.get_cl_num", mock.MagicMock(return_value=mocked_content)):
        manager = InstallManager.factory('Unknown')
        res = manager._load_new_packages(False, sql_version='auto')
        assert res == expected


@pytest.mark.parametrize("mocked_content, expected", [
    ("mysql51", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient18", "mysqlclient15",
                 "libaio.x86_64"]),
    ("mysql55", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "libaio.x86_64"]),
    ("mysql56", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "libaio.x86_64"]),
    ("mysql57", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "numactl-devel.x86_64", "numactl.x86_64", "libaio.x86_64"]),
    ("mysql80", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "numactl-devel.x86_64", "numactl.x86_64", "libaio.x86_64"]),
    ("mariadb55",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb100",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb101",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb102",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb103",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb104",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb105",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb106",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb1011",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("percona56",
     ["cl-Percona-meta", "cl-Percona-meta-client", "cl-Percona-meta-devel", "mysqlclient18", "mysqlclient16",
      "mysqlclient15", "libaio.x86_64"])
])
@mock.patch("modules.base.get_cl_num", mock.MagicMock(return_value=7))
@mock.patch("modules.base.exec_command", mock.MagicMock(return_value=''))
@mock.patch("modules.base.exec_command_out", mock.MagicMock())
@mock.patch("modules.base.download_packages", mock.MagicMock(return_value=True))
@mock.patch("modules.base.cl8_module_enable", mock.MagicMock())
@mock.patch("modules.base.os.uname", mock.MagicMock(return_value=('', 'x86_64')))
@mock.patch("modules.base.urllib.request.urlopen", mock.MagicMock())
@mock.patch("modules.base.write_file", mock.MagicMock())
def test_load_new_packages_version(mocked_content, expected):
    manager = InstallManager.factory('Unknown')
    res = manager._load_new_packages(False, sql_version=mocked_content)
    assert res == expected


@pytest.mark.parametrize("mocked_content, expected", [
    ("mysql51", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient18", "mysqlclient15",
                 "libaio.x86_64"]),
    ("mysql55", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "libaio.x86_64"]),
    ("mysql56", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "libaio.x86_64"]),
    ("mysql57", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "numactl-devel.x86_64", "numactl.x86_64", "libaio.x86_64"]),
    ("mysql80", ["cl-MySQL-meta", "cl-MySQL-meta-client", "cl-MySQL-meta-devel", "mysqlclient16", "mysqlclient15", "mysqlclient18",
                 "numactl-devel.x86_64", "numactl.x86_64", "libaio.x86_64"]),
    ("mariadb55",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb100",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb101",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient18-compat", "mysqlclient21", "libaio.x86_64"]),
    ("mariadb102",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb103",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb104",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb105",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb106",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("mariadb1011",
     ["cl-MariaDB-meta", "cl-MariaDB-meta-client", "cl-MariaDB-meta-devel", "mysqlclient16", "mysqlclient15",
      "mysqlclient21", "libaio.x86_64"]),
    ("percona56",
     ["cl-Percona-meta", "cl-Percona-meta-client", "cl-Percona-meta-devel", "mysqlclient18", "mysqlclient16",
      "mysqlclient15", "libaio.x86_64"])
])
@mock.patch("modules.base.get_cl_num", mock.MagicMock(return_value=8))
@mock.patch("modules.base.exec_command", mock.MagicMock(return_value=''))
@mock.patch("modules.base.exec_command_out", mock.MagicMock())
@mock.patch("modules.base.download_packages", mock.MagicMock(return_value=True))
@mock.patch("modules.base.cl8_module_enable", mock.MagicMock())
@mock.patch("modules.base.os.uname", mock.MagicMock(return_value=('', 'x86_64')))
@mock.patch("modules.base.urllib.request.urlopen", mock.MagicMock())
@mock.patch("modules.base.write_file", mock.MagicMock())
def test_load_new_packages_version_CL8(mocked_content, expected):
    manager = InstallManager.factory('Unknown')
    res = manager._load_new_packages(False, sql_version=mocked_content)
    assert res == expected


@pytest.mark.parametrize("mocked_content, expected", [
    ("mysql51", "cl-mysql-5.1-common.repo"),
    ("mysql55", "cl-mysql-5.5-common.repo"),
    ("mysql56", "cl-mysql-5.6-common.repo"),
    ("mysql57", "cl-mysql-5.7-common.repo"),
    ("mysql80", "cl-mysql-8.0-common.repo"),
    ("mariadb55", "cl-mariadb-5.5-common.repo"),
    ("mariadb100", "cl-mariadb-10.0-common.repo"),
    ("mariadb101", "cl-mariadb-10.1-common.repo"),
    ("mariadb102", "cl-mariadb-10.2-common.repo"),
    ("mariadb103", "cl-mariadb-10.3-common.repo"),
    ("mariadb104", "cl-mariadb-10.4-common.repo"),
    ("mariadb105", "cl-mariadb-10.5-common.repo"),
    ("percona56", "cl-percona-5.6-common.repo")
])
@mock.patch("modules.base.get_cl_num", mock.MagicMock(return_value=7))
@mock.patch("modules.base.exec_command", mock.MagicMock(return_value=''))
@mock.patch("modules.base.exec_command_out", mock.MagicMock())
@mock.patch("modules.base.download_packages", mock.MagicMock(return_value=True))
@mock.patch("modules.base.cl8_module_enable", mock.MagicMock())
@mock.patch("modules.base.os.uname", mock.MagicMock(return_value=('', 'x86_64')))
@mock.patch("modules.base.urllib.request.urlopen", mock.MagicMock())
@mock.patch("modules.base.write_file", mock.MagicMock())
def test_get_repo(mocked_content, expected):
    manager = InstallManager.factory('Unknown')
    res = manager.get_repo_name(sql_version=mocked_content)
    assert res == expected


@pytest.mark.parametrize("mocked_current_version, mocked_version", [
    ('mysql80', 'mariadb100'),
    ('mysql80', 'mariadb101'),
    ('mysql80', 'mariadb102'),
    ('mysql80', 'mariadb103'),
    ('mysql80', 'mariadb104'),
    ('mysql80', 'mariadb105')
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_for_unsupported_db_version(mocked_current_version, mocked_version):
    """
    This test is to check the response of the tested method to an unsupported
    combination of tha database versions (expected "exit 1")
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.base.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._check_mysql_version",
                        return_value={'full':mocked_current_version}):
            with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                            return_value=mocked_version):
                manager = InstallManager.factory('Unknown')
                manager.unsupported_db_version()
    exit_mock.assert_called_once_with(1)


@pytest.mark.parametrize("mocked_current_version, mocked_version", [
    ('mysql80', 'mariadb100'),
    ('mysql80', 'mariadb101'),
    ('mysql80', 'mariadb102'),
    ('mysql80', 'mariadb103'),
    ('mysql80', 'mariadb104'),
    ('mysql80', 'mariadb105')
])
@mock.patch("builtins.open", mock.mock_open(read_data=''))
def test_for_unsupported_db_version_with_force(mocked_current_version, mocked_version):
    """
    This test is to check the response of the tested method to an unsupported
    combination of tha database versions (do nothing cause "force" key is passed)
    """
    exit_mock = mock.MagicMock()
    with mock.patch("modules.base.sys.exit", exit_mock):
        with mock.patch("modules.base.InstallManager._check_mysql_version",
                        return_value={'full':mocked_current_version}):
            with mock.patch("modules.base.InstallManager._get_result_mysql_version",
                            return_value=mocked_version):
                manager = InstallManager.factory('Unknown')
                manager.unsupported_db_version(force=True)
    exit_mock.assert_not_called()
