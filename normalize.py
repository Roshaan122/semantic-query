import json

# filepath: /Users/roshaan/Documents/pd_work/normalize_permits.py
# Load the raw data
with open('top_20_rows.json', 'r') as file:
    raw_data = json.load(file)

# Function to normalize a single permit record
def normalize_permit(record):
    return {
        "permit_number": record.get("permit_number"),
        "permit_type": {
            "code": record.get("permittype"),
            "description": record.get("permit_type_desc")
        },
        "permit_class": {
            "mapped": record.get("permit_class_mapped"),
            "original": record.get("permit_class")
        },
        "work_class": record.get("work_class"),
        "location": {
            "address": record.get("original_address1"),
            "city": record.get("original_city"),
            "state": record.get("original_state"),
            "zip": record.get("original_zip"),
            "latitude": float(record.get("latitude", 0)),
            "longitude": float(record.get("longitude", 0))
        },
        "description": record.get("description"),
        "dates": {
            "applied": record.get("applieddate"),
            "issued": record.get("issue_date"),
            "expires": record.get("expiresdate"),
            "completed": record.get("completed_date")
        },
        "status": {
            "current": record.get("status_current"),
            "status_date": record.get("statusdate")
        },
        "jurisdiction": {
            "council_district": record.get("council_district"),
            "type": record.get("jurisdiction")
        },
        "project_id": record.get("project_id"),
        "link": record.get("link", {}).get("url")
    }

# Normalize all records
normalized_data = [normalize_permit(record) for record in raw_data]

# Save the normalized data to a new file
with open('normalized_permits.json', 'w') as file:
    json.dump(normalized_data, file, indent=4)

print("Normalization complete. Data saved to 'normalized_permits.json'.")