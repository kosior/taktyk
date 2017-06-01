#!/usr/bin/env python3
import os
import sys

if sys.version_info <= (3, 5, 2):
    sys.stdout.write('Program wymaga co najmniej Pythona w wersji 3.5.2\n')
    sys.exit(1)

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__)))))

from taktyk import main


if __name__ == '__main__':
    main()
