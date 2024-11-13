import pytest
from core.models.filetype import FileType

def test_file_type_choices():
    assert FileType.IMAGE == 'image'
    assert FileType.VIDEO == 'video'
    assert FileType.AUDIO == 'audio'

def test_file_type_values():
    assert list(FileType.values) == ['image', 'video', 'audio']

def test_file_type_labels():
    assert list(FileType.labels) == ['Image', 'Video', 'Audio']

def test_file_type_invalid_choice():
    with pytest.raises(ValueError):
        FileType('invalid_choice')