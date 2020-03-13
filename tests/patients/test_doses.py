import six
import pytest
import filecmp
import os

from proknow import ProKnow, Exceptions

def test_download(app, entity_generator, temp_directory):
    pk = app.pk

    dose_path = os.path.abspath("./data/Becker^Matthew/HNC0522c0009_Plan1_Dose.dcm")
    dose = entity_generator(dose_path)

    # Download to directory
    download_path = dose.download(temp_directory.path)
    assert filecmp.cmp(dose_path, download_path, shallow=False)

    # Download to specific file
    specific_path = os.path.join(temp_directory.path, "dose.dcm")
    download_path = dose.download(specific_path)
    assert specific_path == download_path
    assert filecmp.cmp(dose_path, download_path, shallow=False)

    # File does not exist
    with pytest.raises(Exceptions.InvalidPathError) as err_wrapper:
        download_path = dose.download("/path/to/nowhere/dose.dcm")
    assert err_wrapper.value.message == "`/path/to/nowhere/dose.dcm` is invalid"

def test_dose_get_slice_data(app, entity_generator):
    pk = app.pk

    dose_path = os.path.abspath("./data/Becker^Matthew/HNC0522c0009_Plan1_Dose.dcm")
    dose = entity_generator(dose_path)

    data = dose.get_slice_data(0)
    assert isinstance(data, six.binary_type), "data is not binary"

def test_get_analysis(app, workspace_generator):
    pk = app.pk

    directory = os.path.abspath("./data/Becker^Matthew/")
    dose_path = os.path.abspath("./data/Becker^Matthew/HNC0522c0009_Plan1_Dose.dcm")
    _, workspace = workspace_generator()
    batch = pk.uploads.upload(workspace.id, directory)
    dose = batch.find_entity(dose_path).get();

    analysis = dose.get_analysis()
    assert isinstance(analysis["max_dose"], (float,int))
    assert isinstance(analysis["volume"], (float,int))
    assert isinstance(analysis["max_dose_loc"], list)
    for point in analysis["max_dose_loc"]:
        assert isinstance(point, (float,int))
    assert isinstance(analysis["plan"], dict)
    assert isinstance(analysis["curve"], list)
    for point in analysis["curve"]:
        assert isinstance(point, list)
        assert len(point) == 2
    assert isinstance(analysis["rois"], list)
    for roi in analysis["rois"]:
        assert isinstance(roi["id"], six.string_types)
        assert isinstance(roi["name"], six.string_types)
        assert isinstance(roi["dose_grid_bound"], bool)
        assert isinstance(roi["integral_dose"], (float,int))
        assert isinstance(roi["max_dose"], (float,int))
        assert isinstance(roi["mean_dose"], (float,int))
        assert isinstance(roi["min_dose"], (float,int))
        assert isinstance(roi["volume"], (float,int))
        assert isinstance(roi["max_dose_loc"], list)
        for point in roi["max_dose_loc"]:
            assert isinstance(point, (float,int))
        assert isinstance(roi["min_dose_loc"], list)
        for point in roi["min_dose_loc"]:
            assert isinstance(point, (float,int))
        assert isinstance(roi["curve"], list)
        for point in roi["curve"]:
            assert isinstance(point, list)
            assert len(point) == 2

def test_get_analysis_failure(app, entity_generator):
    pk = app.pk

    dose_path = os.path.abspath("./data/Becker^Matthew/HNC0522c0009_Plan1_Dose.dcm")
    dose = entity_generator(dose_path)

    with pytest.raises(AssertionError) as err_wrapper:
        dose.get_analysis()
    assert str(err_wrapper.value) == "Dose analysis not possible"
