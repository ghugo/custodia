# Copyright (C) 2016  Custodia Project Contributors - see LICENSE file
from __future__ import absolute_import

import warnings

import pytest

from custodia.log import ProvisionalWarning

# deprecated APIs raise an exception
warnings.simplefilter('error', category=DeprecationWarning)
# ignore pytest warnings
warnings.filterwarnings('ignore', category=DeprecationWarning,
                        module='_pytest\..*')
# silence our own warnings about provisional APIs
warnings.simplefilter('ignore', category=ProvisionalWarning)


SKIP_SERVERTEST = "--skip-servertests"


def pytest_addoption(parser):
    parser.addoption(
        SKIP_SERVERTEST,
        action="store_true",
        help="Skip integration tests"
    )


def pytest_runtest_setup(item):
    skip_servertest = item.config.getoption(SKIP_SERVERTEST)
    if skip_servertest and item.get_marker("servertest") is not None:
        # args has --skip-servertests and test is marked as servertest
        pytest.skip("Skip integration test")
