import commands
import calendar
import time


def get_time_from_package(pkg):

    modify = get_time('Y', pkg)
    access = get_time('X', pkg)

    return [modify, access]


def get_alternative_pkg(pkg):

    dpkg_command = "dpkg -L {0}| grep /usr/bin/"
    dpkg_command += " || dpkg -L {0}| grep /usr/sbin/"
    bin_path = '/usr/bin'
    pkg_bin = commands.getoutput(dpkg_command.format(pkg))

    for pkg_path in pkg_bin.splitlines():

        if bin_path in pkg_path:
            return pkg_path
        elif pkg in pkg_path:
            return pkg_path

    return None


def get_time(option, pkg):

    stat_base = "stat -c '%{option}' `which {package}`"
    stat_error = 'stat: missing operand'
    stat_time = stat_base.format(option=option, package=pkg)

    pkg_time = commands.getoutput(stat_time)

    return pkg_time if not pkg_time.startswith(stat_error) else None


def linear_percent_function(modify, access, time_now):
    modify, access = int(modify), int(access)

    time_access = access - modify
    time_actual = time_now - modify

    percent = float(time_access) / float(time_actual)

    return percent


def get_pkg_time_weight(pkg):
    modify, access = (get_time_from_package(pkg) or
                      get_time_from_package(get_alternative_pkg(pkg)) or
                      [None, None])

    if not modify and not access:
        return 1.0

    time_now = calendar.timegm(time.gmtime())

    return linear_percent_function(modify, access, time_now)
