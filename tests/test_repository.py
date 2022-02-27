import logging
from contextlib import nullcontext as does_not_raise

import pytest

from dynoscale.repository import DynoscaleRepository, Record, RecordOut, RecordIn

logging.basicConfig(level=logging.DEBUG)


# ========================= TESTS =============================

@pytest.mark.parametrize(
    "records,expectation",
    [
        (True, does_not_raise()),
        (False, does_not_raise()),
        (0, does_not_raise()),
        (1, does_not_raise()),
        (-1, does_not_raise()),
        (0.1, does_not_raise()),
        (-0.1, does_not_raise()),
        ("abc", does_not_raise()),
        ("", does_not_raise()),
        ([], does_not_raise()),
        ((), does_not_raise()),
        ({}, does_not_raise()),
        ([1], does_not_raise()),
        ((1,), does_not_raise()),
        ({1: 1, "1": "1"}, does_not_raise()),
        ((RecordOut(-0, 0, "", "", row_id=-0.5)), does_not_raise()),
        ((RecordOut(-0, 0, "Y", "U", row_id="ffs")), does_not_raise()),
        ((RecordIn(-0, 0, "NO", "DIE")), does_not_raise()),
        # ([], pytest.raises(ZeroDivisionError)),
    ],
)
def test_repo_checks_input(ds_repository, records, expectation):
    with expectation:
        ds_repository.delete_records(records=records)


def test_repo_adding_records(repo_path):
    rng = 10
    a = DynoscaleRepository(path=repo_path)
    b = DynoscaleRepository(path=repo_path)
    records = [Record(1, 1, "", "") for i in range(rng)]
    for i, r in enumerate(records):
        (a if i % 2 else b).add_record(r)
    ra = a.get_all_records()
    assert len(ra) == rng
    rb = a.get_all_records()
    assert len(rb) == rng
    assert ra == rb


def test_repo_deleting_records(repo_path):
    rng = 5
    a = DynoscaleRepository(path=repo_path)
    b = DynoscaleRepository(path=repo_path)
    records = [Record(1, 1, "", "") for i in range(rng)]
    map(a.add_record, records)
    b.delete_records(a.get_all_records())
    assert len(a.get_all_records()) == 0
    assert len(b.get_all_records()) == 0
