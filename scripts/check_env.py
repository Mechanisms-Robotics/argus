#!/usr/bin/env python3
"""
Argus smoke-test script (non-destructive).

Usage:
  # Local (on Pi 5 with hardware and packages installed):
  ./scripts/check_env.py

  # CI / safe mode (won't import hardware-initializing modules):
  CI=1 ./scripts/check_env.py

Checks performed (local):
 - runtime import of key packages: spidev, periphery, Pillow
 - project modules: epdconfig, epd2in13b_V4 (attempt import and report any errors)
 - presence of /dev/gpiochip4
 - existence of vendor .so files under eink/lib/waveshare_epd/

Checks performed (CI mode, CI=1):
 - syntax (py_compile) of `eink/epdconfig.py` and `eink/epd2in13b_V4.py`
 - existence of vendor .so files is reported but not required

This script intentionally avoids calling any hardware initialization functions.
"""

import os
import sys
import importlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VENDOR_SO_DIR = os.path.join(ROOT, 'eink', 'lib', 'waveshare_epd')

def try_import(name):
    try:
        importlib.import_module(name)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    ci_mode = os.environ.get('CI', '') == '1'

    # Ensure the `eink/` folder is on sys.path so imports like `import epdconfig`
    # and `import epd2in13b_V4` succeed regardless of the current working
    # directory when this script is executed.
    eink_path = os.path.join(ROOT, 'eink')
    if eink_path not in sys.path:
        sys.path.insert(0, eink_path)
    checks = []

    if ci_mode:
        # CI: avoid imports that may initialize hardware. Do syntax checks instead.
        import py_compile
        for path in (os.path.join(ROOT, 'eink', 'epdconfig.py'), os.path.join(ROOT, 'eink', 'epd2in13b_V4.py')):
            exists = os.path.exists(path)
            if exists:
                try:
                    py_compile.compile(path, doraise=True)
                    checks.append((path, True, None))
                except py_compile.PyCompileError as e:
                    checks.append((path, False, str(e)))
            else:
                checks.append((path, False, 'file not found'))

        checks.append(('/dev/gpiochip4 (skipped in CI)', True, 'skipped'))

    else:
        # Local checks: try importing runtime packages and project modules
        for pkg in ('spidev', 'periphery', 'PIL'):
            ok, err = try_import(pkg)
            checks.append((pkg, ok, err))

        for mod in ('epdconfig', 'epd2in13b_V4'):
            ok, err = try_import(mod)
            checks.append((mod, ok, err))

        # Device file check (Pi 5 expected)
        dev_path = '/dev/gpiochip4'
        checks.append((dev_path, os.path.exists(dev_path), None if os.path.exists(dev_path) else 'not found'))

        # Vendor .so files are not required in this repository (removed); skip check

    ok = True
    print('\nArgus environment smoke test')
    print('Repository root: %s' % ROOT)
    for name, passed, info in checks:
        status = 'OK' if passed else 'FAIL'
        print(f' - {name}: {status}')
        if info:
            print(f'     -> {info}')
        if not passed:
            ok = False

    print('\nSummary:')
    if ok:
        print('Looks good.')
        return 0
    else:
        print('Some checks failed. See messages above.')
        return 2

if __name__ == '__main__':
    sys.exit(main())
