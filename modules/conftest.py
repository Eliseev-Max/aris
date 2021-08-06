import time
from typing_extensions import Literal
import pytest

def pytest_addoption(parser):
    """PyTest method for adding custom console parameters"""

    parser.addoption("--t1_SERVER", action="store", default=15, type=int,
                     help="Set additional value for timestamp")
    parser.addoption("--t2_SERVER", action="store", default=10, type=int,
                     help="Set additional value for timestamp")
    parser.addoption("--t3_SERVER", action="store", default=20, type=int,
                     help="Set additional value for timestamp")
    parser.addoption("--W_SERVER", action="store", default=8, type=int,
                     help="Set additional value for timestamp")
    parser.addoption("--det", action="store", default=2, type=int,
                     help="Set additional value for timestamp")
    parser.addoption("--IP", action="store", default="10.1.31.10", type=str,
                     help="Set additional value for timestamp")     
    parser.addoption("--PORT", action="store", default=2404, type=str,
                     help="Set additional value for timestamp")

@pytest.fixture(scope="session")
def t1_SERVER(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--t1_SERVER")

@pytest.fixture(scope="session")
def t2_SERVER(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--t2_SERVER")

@pytest.fixture(scope="session")
def t3_SERVER(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--t3_SERVER")


@pytest.fixture(scope="session")
def W_SERVER(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--W_SERVER")

@pytest.fixture(scope="session")
def det(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--det")

@pytest.fixture(scope="session")
def IP(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--IP")


@pytest.fixture(scope="session")
def PORT(request):
    """Handler for --additional_value parameter"""

    return request.config.getoption("--PORT")
