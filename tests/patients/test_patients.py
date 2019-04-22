import pytest
import re
import os
import filecmp
import six

from proknow import Exceptions

def test_create(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()

    # Verify returned PatientItem
    patient = pk.patients.create(workspace.id, "1000", "Last^First", "2018-01-01", "123456.000000", "M")
    assert patient.mrn == "1000"
    assert patient.name == "Last^First"
    assert patient.birth_date == "2018-01-01"
    assert patient.birth_time == "123456.000000"
    assert patient.sex == "M"

    # Assert item can be found in query
    patients = pk.patients.query(workspace.id)
    for patient in patients:
        if patient.mrn == "1000":
            patient_match = patient
            break
    else:
        patient_match = None
    assert patient_match is not None
    assert patient_match.mrn == "1000"
    assert patient_match.name == "Last^First"
    assert patient_match.birth_date == "2018-01-01"
    assert patient_match.birth_time == "123456.000000"
    assert patient_match.sex == "M"

def test_create_failure(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()

    pk.patients.create(workspace.id, "1000", "Last^First")

    with pytest.raises(Exceptions.HttpError) as err_wrapper:
        pk.patients.create(workspace.id, "1000", "Last^First")
    assert err_wrapper.value.status_code == 409
    assert err_wrapper.value.body == 'Patient already exists with mrn "1000"'

def test_delete(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()

    patient = pk.patients.create(workspace.id, "1000", "Last^First")

    # Verify patient was deleted successfully
    patient.delete()
    for patient in pk.patients.query(workspace.id):
        if patient.mrn == "1000":
            match = patient
            break
    else:
        match = None
    assert match is None

def test_delete_failure(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()

    patient = pk.patients.create(workspace.id, "1000", "Last^First")
    patient.delete()

    # Assert error is raised when attempting to delete patient that does not exist
    with pytest.raises(Exceptions.HttpError) as err_wrapper:
        patient.delete()
    assert err_wrapper.value.status_code == 404
    assert err_wrapper.value.body == 'Patient "' + patient.id + '" not found'

def test_find(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()
    pk.patients.create(workspace.id, "1000", "Last^First")
    expr = re.compile(r"st\^Fi")

    # Find with no args
    found = pk.patients.find(workspace.id)
    assert found is None

    # Find using predicate
    found = pk.patients.find(workspace.id, lambda p: expr.search(p.data["name"]) is not None)
    assert found is not None
    assert found.mrn == "1000"
    assert found.name == "Last^First"
    assert found.birth_date == None
    assert found.birth_time == None
    assert found.sex == None

    # Find using props
    found = pk.patients.find(workspace.id, mrn="1000", name="Last^First")
    assert found is not None
    assert found.mrn == "1000"
    assert found.name == "Last^First"
    assert found.birth_date == None
    assert found.birth_time == None
    assert found.sex == None

    # Find using both
    found = pk.patients.find(workspace.id, lambda p: expr.search(p.data["name"]) is not None, mrn="1000", name="Last^First")
    assert found is not None
    assert found.mrn == "1000"
    assert found.name == "Last^First"
    assert found.birth_date == None
    assert found.birth_time == None
    assert found.sex == None

    # Find failure
    found = pk.patients.find(workspace.id, lambda p: expr.search(p.data["mrn"]) is not None)
    assert found is None
    found = pk.patients.find(workspace.id, mrn="1000", name="last^first")
    assert found is None

def test_lookup(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()
    pk.patients.create(workspace.id, "1000", "Test^1", "2018-01-01", "123456.000000", "M")
    pk.patients.create(workspace.id, "1001", "Test^2")

    patients = pk.patients.lookup(workspace.id, ["1000", "1001"])
    assert len(patients) == 2
    for patient in patients:
        if patient.mrn == "1000":
            assert patient.mrn == "1000"
            assert patient.name == "Test^1"
            assert patient.birth_date == "2018-01-01"
            assert patient.birth_time == "123456.000000"
            assert patient.sex == "M"
        elif patient.mrn == "1001":
            assert patient.mrn == "1001"
            assert patient.name == "Test^2"
            assert patient.birth_date == None
            assert patient.birth_time == None
            assert patient.sex == None

def test_query(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()

    pk.patients.create(workspace.id, "1000", "Test^1", "2018-01-01", "123456.000000", "M")
    pk.patients.create(workspace.id, "1001", "Test^2")

    # Verify test 1
    for patient in pk.patients.query(workspace.id):
        if patient.mrn == "1000":
            match = patient
            break
    else:
        match = None
    assert match is not None
    assert isinstance(match.id, six.string_types)
    assert match.mrn == "1000"
    assert match.name == "Test^1"
    assert match.birth_date == "2018-01-01"
    assert match.birth_time == "123456.000000"
    assert match.sex == "M"

    # Verify test 2
    for patient in pk.patients.query(workspace.id):
        if patient.mrn == "1001":
            match = patient
            break
    else:
        match = None
    assert match is not None
    assert isinstance(match.id, six.string_types)
    assert match.mrn == "1001"
    assert match.name == "Test^2"
    assert match.birth_date == None
    assert match.birth_time == None
    assert match.sex == None

def test_update(app, custom_metric_generator, workspace_generator):
    pk = app.pk

    _, custom_metric_string = custom_metric_generator(type={"string": {}})
    _, custom_metric_number = custom_metric_generator(type={"number": {}})
    _, custom_metric_enum = custom_metric_generator(type={"enum": {"values": ["one", "two"]}})
    _, workspace = workspace_generator(("update-patients-test", "Update Patients Test", False))
    patient = pk.patients.create(workspace.id, "1000", "Last^First")

    # Verify patient was updated successfully
    patient.mrn = "1000-AAAA-2000"
    patient.name = "Modified^Name"
    patient.birth_date = "2018-01-01"
    patient.birth_time = "123456.000000"
    patient.sex = "M"
    meta = patient.get_metadata()
    meta[custom_metric_string.name] = "test"
    meta[custom_metric_number.name] = 42
    meta[custom_metric_enum.name] = "one"
    patient.set_metadata(meta)
    patient.save()
    patients = pk.patients.query(workspace.id)
    for patient in patients:
        if patient.mrn == "1000-AAAA-2000":
            patient_match = patient
            break
    else:
        patient_match = None
    assert patient_match is not None
    patient_item = patient_match.get()
    assert patient_item.mrn == "1000-AAAA-2000"
    assert patient_item.name == "Modified^Name"
    assert patient_item.birth_date == "2018-01-01"
    assert patient_item.birth_time == "123456.000000"
    assert patient_item.sex == "M"
    assert patient_item.get_metadata() == {
        custom_metric_string.name: "test",
        custom_metric_number.name: 42,
        custom_metric_enum.name: "one"
    }

def test_update_failure(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()
    patient1 = pk.patients.create(workspace.id, "1000", "Last^First")
    patient2 = pk.patients.create(workspace.id, "1001", "Last^First")

    with pytest.raises(Exceptions.HttpError) as err_wrapper:
        patient1.mrn = "1001"
        patient1.save()
    assert err_wrapper.value.status_code == 409
    assert err_wrapper.value.body == 'Patient already exists with mrn "1001"'

def test_set_metadata_failure(app, workspace_generator):
    pk = app.pk

    _, workspace = workspace_generator()
    patient = pk.patients.create(workspace.id, "1000", "Last^First")
    meta = patient.get_metadata()
    meta["Unknown Metric"] = "test"

    with pytest.raises(Exceptions.CustomMetricLookupError) as err_wrapper:
        patient.set_metadata(meta)
    assert err_wrapper.value.message == 'Custom metric with name `Unknown Metric` not found.'

def test_find_entities(app, patient_generator):
    pk = app.pk

    patient = patient_generator("./tests/data/Becker^Matthew")

    # Find with no args
    entities = patient.find_entities()
    assert len(entities) == 0

    # Find image set
    entities = patient.find_entities(lambda entity: entity.data["type"] == "image_set")
    assert len(entities) == 1
    entities = patient.find_entities(type="image_set")
    assert len(entities) == 1

    # Find structure set
    entities = patient.find_entities(lambda entity: entity.data["type"] == "structure_set")
    assert len(entities) == 1
    entities = patient.find_entities(type="structure_set")
    assert len(entities) == 1

    # Find plan
    entities = patient.find_entities(lambda entity: entity.data["type"] == "plan")
    assert len(entities) == 1
    entities = patient.find_entities(type="plan")
    assert len(entities) == 1

    # Find dose
    entities = patient.find_entities(lambda entity: entity.data["type"] == "dose")
    assert len(entities) == 1
    entities = patient.find_entities(type="dose")
    assert len(entities) == 1

    # Find multiple
    entities = patient.find_entities(lambda entity: True)
    assert len(entities) == 4
    entities = patient.find_entities(lambda entity: entity.data["type"] == "dose" or entity.data["type"] == "plan")
    assert len(entities) == 2