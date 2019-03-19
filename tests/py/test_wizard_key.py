import pytest
import utilities


@pytest.mark.parametrize("mocked_version, expected", [
    ('5.5.61', 61),
    ('10.0.0', 0),
    ('10.1.30', 30),
    ('10.2.22', 22),
    ('10.3.3', 3),
    ('5.6.41', 41),
    ('5.7.25', 25),
    ('8.0.15', 15),
])
def test_get_release_num(mocked_version, expected):
    assert utilities.get_release_num(mocked_version) == expected


@pytest.mark.parametrize("mocked_new, mocked_prev, expected_res, expected_msg", [
    ({'new_type': 'mariadb', 'new_ver': '10.3.13', 'new_short': '10.3'}, {'short': '10.3', 'mysql_type': 'mariadb', 'full': 'mariadb103', 'extended': '10.3.13'}, True, ''),
    ({'new_type': 'mariadb', 'new_ver': '10.2.22', 'new_short': '10.2'}, {'short': '10.2', 'mysql_type': 'mariadb', 'full': 'mariadb102', 'extended': '10.2.21'}, True, ''),
    ({'new_type': 'mariadb', 'new_ver': '10.3.13', 'new_short': '10.3'}, {}, False, 'Failed to retrieve current mysql version'),
    ({'new_type': 'mysql', 'new_ver': '5.7.25', 'new_short': '5.7'}, {'short': '5.5', 'mysql_type': 'mariadb', 'full': 'mariadb55', 'extended': '5.5.61'}, False, 'change MySQL version'),
    ({'new_type': 'mariadb', 'new_ver': '10.2.22', 'new_short': '10.2'}, {'short': '10.2', 'mysql_type': 'mariadb', 'full': 'mariadb102', 'extended': '10.2.23'}, False, 'attempting to install a LOWER'),
    ({'new_type': 'mariadb', 'new_ver': '10.2.22', 'new_short': '10.2'}, {'short': '10.2', 'mysql_type': 'mariadb', 'full': 'mariadb102', 'extended': '10.2.3'}, False, 'update your database packages'),
    ({'new_type': 'mariadb', 'new_ver': '10.2.22', 'new_short': '10.2'}, {'short': '10.1', 'mysql_type': 'mariadb', 'full': 'mariadb101', 'extended': '10.0.36'}, False, 'change mariadb version from 10.0.36 to 10.2.22'),
    ({'new_type': 'mariadb', 'new_ver': '10.2.22', 'new_short': '10.2'}, {'short': '10.1', 'mysql_type': 'mariadb', 'full': 'mariadb101', 'extended': '10.1.21'}, False, 'change mariadb version from 10.1.21 to 10.2.22'),
    ({'new_type': 'mariadb', 'new_ver': '10.0.36', 'new_short': '10.0'}, {'short': '10.1', 'mysql_type': 'mariadb', 'full': 'mariadb101', 'extended': '10.1.21'}, False, 'change mariadb version from 10.1.21 to 10.0.36'),
])
def test_wizard_install_confirm(mocked_new, mocked_prev, expected_res, expected_msg, capsys):
    result = utilities.wizard_install_confirm(mocked_new, mocked_prev)
    out, err = capsys.readouterr()
    assert result is expected_res
    assert expected_msg in out
