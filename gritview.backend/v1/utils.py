import re

# Helper function that splits course_name to (name, catalog_number)
# example: 'CMSC202' -> (CMSC, 202)
def split_alphanumeric(string):
    match = re.match(r"([a-z]+)([0-9]+)", string, re.I)
    if not match:
        return None
    return match.groups()