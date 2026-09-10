"""
generate_entities.py

Generates synthetic "entities" for a case: people, phone numbers, vehicles,
and organizations. This is step 1 of the seed pipeline — generate_network.py
consumes the output of this script to build relationships between entities.

Usage:
    python generate_entities.py --num-people 40 --case-id case_001

Output:
    data/processed/entities.json
    Shape:
    {
        "case_id": "case_001",
        "entities": [
            {
                "id": "person_0001",
                "type": "person",
                "label": "Jane Doe",
                "attributes": {...}
            },
            ...
        ]
    }
"""

import argparse
import json
import random
import uuid
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "processed"
OUTPUT_FILE = OUTPUT_DIR / "entities.json"


def make_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:04d}"


def generate_people(n: int) -> list[dict]:
    people = []
    for i in range(n):
        gender = random.choice(["male", "female"])
        name = fake.name_male() if gender == "male" else fake.name_female()
        people.append(
            {
                "id": make_id("person", i),
                "type": "person",
                "label": name,
                "attributes": {
                    "gender": gender,
                    "age": random.randint(18, 70),
                    "occupation": fake.job(),
                    "address": fake.address().replace("\n", ", "),
                    "national_id": fake.unique.bothify(text="??######", letters="ABCDEFGHIJ"),
                    "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=70).isoformat(),
                    "flagged": False,  # default; overridden for planted cluster members later
                },
            }
        )
    return people


def generate_phones(people: list[dict], min_per_person=1, max_per_person=2) -> list[dict]:
    phones = []
    counter = 0
    for person in people:
        num_phones = random.randint(min_per_person, max_per_person)
        for _ in range(num_phones):
            phones.append(
                {
                    "id": make_id("phone", counter),
                    "type": "phone",
                    "label": fake.phone_number(),
                    "attributes": {
                        "owner_id": person["id"],
                        "carrier": random.choice(["Airtel", "Jio", "Vodafone Idea", "BSNL"]),
                        "imei": fake.numerify(text="##############"),
                        "activated_on": fake.date_between(start_date="-5y", end_date="today").isoformat(),
                    },
                }
            )
            counter += 1
    return phones


def generate_vehicles(people: list[dict], ownership_rate: float = 0.5) -> list[dict]:
    vehicles = []
    counter = 0
    makes_models = [
        ("Maruti Suzuki", "Swift"),
        ("Hyundai", "Creta"),
        ("Honda", "City"),
        ("Tata", "Nexon"),
        ("Royal Enfield", "Classic 350"),
        ("Toyota", "Innova"),
        ("Mahindra", "XUV700"),
    ]
    for person in people:
        if random.random() < ownership_rate:
            make, model = random.choice(makes_models)
            vehicles.append(
                {
                    "id": make_id("vehicle", counter),
                    "type": "vehicle",
                    "label": f"{make} {model}",
                    "attributes": {
                        "owner_id": person["id"],
                        "plate_number": fake.bothify(text="??-##-??-####").upper(),
                        "color": fake.color_name(),
                        "registered_on": fake.date_between(start_date="-8y", end_date="today").isoformat(),
                    },
                }
            )
            counter += 1
    return vehicles


def generate_orgs(n: int) -> list[dict]:
    org_types = ["Shell Company", "Trading Firm", "NGO", "Logistics Company", "Retail Business"]
    orgs = []
    for i in range(n):
        orgs.append(
            {
                "id": make_id("org", i),
                "type": "organization",
                "label": fake.company(),
                "attributes": {
                    "org_type": random.choice(org_types),
                    "registration_number": fake.bothify(text="REG-#######"),
                    "registered_address": fake.address().replace("\n", ", "),
                    "incorporated_on": fake.date_between(start_date="-15y", end_date="-1y").isoformat(),
                },
            }
        )
    return orgs


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic entities for NetTrace")
    parser.add_argument("--num-people", type=int, default=40, help="Number of people to generate")
    parser.add_argument("--num-orgs", type=int, default=6, help="Number of organizations to generate")
    parser.add_argument("--case-id", type=str, default="case_001", help="Case identifier")
    args = parser.parse_args()

    people = generate_people(args.num_people)
    phones = generate_phones(people)
    vehicles = generate_vehicles(people)
    orgs = generate_orgs(args.num_orgs)

    entities = people + phones + vehicles + orgs

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "case_id": args.case_id,
        "generated_id": str(uuid.uuid4()),
        "counts": {
            "people": len(people),
            "phones": len(phones),
            "vehicles": len(vehicles),
            "organizations": len(orgs),
            "total": len(entities),
        },
        "entities": entities,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(entities)} entities for case '{args.case_id}'")
    print(f"  people={len(people)} phones={len(phones)} vehicles={len(vehicles)} orgs={len(orgs)}")
    print(f"Wrote: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
