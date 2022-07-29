# coding=utf-8
import os
import sys

# because wg uses protocol in a really strange way
# and passes pickes in it
FIXTURES_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')
sys.path.append(FIXTURES_PATH)
