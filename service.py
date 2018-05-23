import os, subprocess

def start(name):
    """Start a system service"""
    return service('start', name)


def stop(name):
    """Stop a system service"""
    return service('stop', name)


def restart(name):
    """Restart a system service"""
    return service('restart', name)

def reload(name, restart_on_failure=False):
    """Reload a system service, optionally falling back to restart if
    reload fails"""
    result = service('reload', name)
    if not result and restart_on_failure:
        result = service('restart', name)
    return result
    
def pause(name, init_dir="/etc/init", initd_dir="/etc/init.d"):
    """Pause a system service.
    Stop it, and prevent it from starting again at boot."""
    stopped = True
    if running(name):
        stopped = stop(name)
    upstart_file = os.path.join(init_dir, "{}.conf".format(name))
    sysv_file = os.path.join(initd_dir, name)
    if init_is_systemd():
        service('disable', name)
    elif os.path.exists(upstart_file):
        override_path = os.path.join(
            init_dir, '{}.override'.format(name))
        with open(override_path, 'w') as fh:
            fh.write("manual\n")
    elif os.path.exists(sysv_file):
        subprocess.check_call(["update-rc.d", name, "disable"])
    else:
        raise ValueError(
            "Unable to detect {0} as SystemD, Upstart {1} or"
            " SysV {2}".format(
                name, upstart_file, sysv_file))
    return stopped


def resume(name, init_dir="/etc/init",
                   initd_dir="/etc/init.d"):
    """Resume a system service.
    Reenable starting again at boot. Start the service"""
    upstart_file = os.path.join(init_dir, "{}.conf".format(name))
    sysv_file = os.path.join(initd_dir, name)
    if init_is_systemd():
        service('enable', name)
    elif os.path.exists(upstart_file):
        override_path = os.path.join(
            init_dir, '{}.override'.format(name))
        if os.path.exists(override_path):
            os.unlink(override_path)
    elif os.path.exists(sysv_file):
        subprocess.check_call(["update-rc.d", name, "enable"])
    else:
        raise ValueError(
            "Unable to detect {0} as SystemD, Upstart {1} or"
            " SysV {2}".format(
                name, upstart_file, sysv_file))

    started = running(name)
    if not started:
        started = start(name)
    return started


def service(action, name):
    """Control a system service"""
    if init_is_systemd():
        cmd = ['systemctl', action, name]
    else:
        cmd = ['service', name, action]
    return subprocess.call(cmd) == 0

def systemv_services_running():
    output = subprocess.check_output(
        ['service', '--status-all'],
        stderr=subprocess.STDOUT).decode('UTF-8')
    return [row.split()[-1] for row in output.split('\n') if '[ + ]' in row]


def running(name):
    """Determine whether a system service is running"""
    if init_is_systemd():
        return service('is-active', name)
    else:
        try:
            output = subprocess.check_output(
                ['service', name, 'status'],
                stderr=subprocess.STDOUT).decode('UTF-8')
        except subprocess.CalledProcessError:
            return False
        else:
            # This works for upstart scripts where the 'service' command
            # returns a consistent string to represent running 'start/running'
            if ("start/running" in output or "is running" in output or
                    "up and running" in output):
                return True
            # Check System V scripts init script return codes
            if name in systemv_services_running():
                return True
            return False


def available(name):
    """Determine whether a system service is available"""
    try:
        subprocess.check_output(
            ['service', name, 'status'],
            stderr=subprocess.STDOUT).decode('UTF-8')
    except subprocess.CalledProcessError as e:
        return b'unrecognized service' not in e.output
    else:
        return True


SYSTEMD_SYSTEM = '/run/systemd/system'


def init_is_systemd():
    """Return True if the host system uses systemd, False otherwise."""
    return os.path.isdir(SYSTEMD_SYSTEM)
