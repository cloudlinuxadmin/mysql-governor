import mock
import pytest
import utilities


def test_exec_command_with_timeout_fail(monkeypatch):
    """
    When hit timeout, the RuntimeError is raised
    """
    monkeypatch.setattr('utilities.fDEBUG_FLAG', True)
    with pytest.raises(RuntimeError):
        utilities.exec_command_with_timeout('sleep 10', timeout=2)


def test_exec_command_with_timeout_success(monkeypatch, capfd):
    """
    When command executed successfully, the output goes to standard stream
    Also testing consuming of generated commands
    """
    msg = 'Hello, world!'
    monkeypatch.setattr('utilities.fDEBUG_FLAG', True)
    utilities.exec_command_with_timeout('echo %s' % msg)
    out, err = capfd.readouterr()
    assert msg in out


conf1 = """
[client-server]
!includedir /etc/my.cnf.d
"""
conf2 = """
[mysqld]
pid-file=/var/run/mysqld/mysqld.pid
default-storage-engine=MyISAM
innodb_file_per_table=1
"""
conf3 = """
[mysqld]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
default-storage-engine=MyISAM
"""
conf4 = """
[mysqld]
performance-schema=0
datadir=/var/lib/mysql
performance-schema=0
log-error=/var/log/mysqld.log
"""


@pytest.mark.parametrize("mocked_content, expected", [
    (conf1, ''),
    (conf2, ''),
    (conf3, '/var/log/mysqld.log'),
    (conf4, '/var/log/mysqld.log')
], ids=['no_section', 'no_option', 'str_option', 'duplicated_options'])
def test_get_mysql_cnf_value(mocked_content, expected, option='log-error'):
    """
    Read log-error option from given example of /etc/my.cnf
    """
    with mock.patch('builtins.open', mock.mock_open(read_data=mocked_content)):
        assert utilities.get_mysql_cnf_value('mysqld', option) == expected


@pytest.mark.parametrize("mocked_content", [conf1, conf4], ids=['simple_options', 'duplicated_options'])
def test_read_config(mocked_content):
    """
    Test reading config files
    """
    with mock.patch('builtins.open', mock.mock_open(read_data=mocked_content)):
        assert utilities.read_config_file('')
