import json

# Load the JSON file
file_path = "top_20_rows.json"
with open(file_path, "r") as file:
    data = json.load(file)

# Extract descriptions and their lengths
descriptions = [(index, item, len(item.get("description", ""))) for index, item in enumerate(data)]

# Sort by length of description in descending order
sorted_descriptions = sorted(descriptions, key=lambda x: x[2], reverse=True)

# Get the top 3 entries
top_3 = sorted_descriptions[:3]

# Prepare the top 3 data for JSON output (full details)
top_3_data = [item for _, item, _ in top_3]

# Save the top 3 results to a new JSON file
output_file_path = "top_3_descriptions_full.json"
with open(output_file_path, "w") as output_file:
    json.dump(top_3_data, output_file, indent=4)

# Print confirmation
print(f"Top 3 full details saved to {output_file_path}")