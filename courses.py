import csv

def load_courses():
    courses = {}
    with open("courses.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["department"].upper(), row["code"].upper())
            courses[key] = row["name"]
    return courses