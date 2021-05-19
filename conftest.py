import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--ip",
        action = "store",
        type = str,
        default = "10.1.32.253",
        help="Set IP-address of testing ARIS Server"
    )

    parser.addoption(
        "--write_log",
        action = "store_true",
        help="If parameter exists, the logfile will be created"
    )

    parser.addoption(
        "--csv",
        action = "store_true",
        help="If parameter exists, the csv-file with sequence of events  will be created"
    )

    parser.addoption(
        "--k_param",
        type = int,
        default=12,
        help="Server parameter K"
    )


@pytest.fixture
def ip(request):
    return request.config.getoption("--ip")


@pytest.fixture
def write_log(request):
    return request.config.getoption("--write_log")

@pytest.fixture
def csv(request):
    return request.config.getoption("--csv")


@pytest.fixture
def K_parameter(request):
    return request.config.getoption("--k_param")
