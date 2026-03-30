#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
sys.argv = ['vsh_cli.py', 'scan-file', '../test/samples/vuln_project/sqli.py', '--format', 'summary']
from scripts.vsh_cli import main
try:
    main()
except SystemExit:
    pass
