import os
import pytest
import mock
import dbgovernor_map
import dbgovernor_map_plesk


@pytest.mark.skip(reason="Caused by Build System regression AL-4801")
def test_mysqldb_error_da(capsys):
    with mock.patch('dbgovernor_map.get_dauser', return_value=dict()):
        dbgovernor_map.get_account_list(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'da_mysql.conf'))
        out, err = capsys.readouterr()
        assert "Can't connect" in out


@pytest.mark.skip(reason="Caused by Build System regression AL-4801")
def test_mysqldb_error_plesk(capsys):
    with mock.patch('dbgovernor_map_plesk.read_mysql_conn_params', return_value={'login': '', 'pass': ''}):
        dbgovernor_map_plesk.get_users_data()
        out, err = capsys.readouterr()
        assert "Can't connect" in out
