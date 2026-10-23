import copy
from pathlib import Path

import pytest
from auditbank.parse import parse_file

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_report():
    return copy.deepcopy(parse_file(FIXTURES / "minimal-valid.md"))
