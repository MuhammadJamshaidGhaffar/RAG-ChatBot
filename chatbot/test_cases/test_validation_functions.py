import re

FACULTIES = [
    "oral and dental",
    "pharmacy",
    "commerce and business administration",
    "engineering",
    "computer science",
    "economics and political science"
]

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_mobile(mobile):
    return re.match(r"^\+?\d{10,15}$", mobile) is not None

def is_valid_faculty(faculty):
    return faculty.lower() in [f.lower() for f in FACULTIES]

# write test cases for the above functions
def test_is_valid_email():
    assert is_valid_email("muhammadjam@gmail.com") == True
    assert is_valid_email("muhammadjam@gmail") == False
    assert is_valid_email("muhammadjam.com") == False
def test_is_valid_mobile():
    assert is_valid_mobile("+923001234567") == True
    assert is_valid_mobile("3001234567") == True
    assert is_valid_mobile("30012345") == False
    assert is_valid_mobile("3001234567890123456789") == False

def test_is_valid_faculty():
    assert is_valid_faculty("oral and dental") == True
    assert is_valid_faculty("Pharmacy") == True
    assert is_valid_faculty("unknown faculty") == False
    assert is_valid_faculty("Engineering") == True

test_is_valid_email()
test_is_valid_mobile()
test_is_valid_faculty()
