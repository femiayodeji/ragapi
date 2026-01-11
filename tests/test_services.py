import pytest
from app.core.query_validator import validator
from app.models import Query
from pydantic import ValidationError

def test_query_validator_basic():
    assert validator.validate_basic("What is a passport?") is None
    assert validator.validate_basic("") is not None
    assert validator.validate_basic("a") is not None

def test_query_model():
    query = Query(question="What is a passport?")
    assert query.question == "What is a passport?"
    
    query = Query(question="  Test  ")
    assert query.question == "Test"
    
    with pytest.raises(ValidationError):
        Query(question="")
    
    with pytest.raises(ValidationError):
        Query(question="x" * 6000)
