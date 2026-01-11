import pytest
import os
from app.services.document_processor import file_hash, get_pdf_files

def test_get_pdf_files():
    files = get_pdf_files()
    assert isinstance(files, list)

def test_file_hash():
    test_file = "test_temp.txt"
    with open(test_file, 'w') as f:
        f.write("test content")
    
    hash1 = file_hash(test_file)
    hash2 = file_hash(test_file)
    assert hash1 == hash2
    
    os.remove(test_file)
