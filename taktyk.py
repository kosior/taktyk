#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

if sys.version_info <= (3, 5, 2):
    sys.stdout.write('Program wymaga co najmniej Pythona w wersji 3.5.2\n')
    sys.stdout.write('Naciśnij ENTER, aby wyjść.')
    sys.stdin.read(1)
    sys.exit(1)

from taktyk import main, settings

if __name__ == '__main__':
    if len(sys.argv) == 1:
        args = input('Możesz podać argumenty (ENTER, aby kontynuować): ')
        if args:
            settings.STATIC_ARGS = args.split(' ')
    try:
        main()
    except SystemExit:
        pass
    finally:
        input('Naciśnij ENTER, aby wyjść.')
