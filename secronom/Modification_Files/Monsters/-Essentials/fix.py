import json
import sys

def load_json(file_path):
    """Load EOC data from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """Save EOC data to a JSON file (pretty-printed)."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def gather_eoc_dict(json_data):
    """
    Return a dict:
      eoc_dict[eoc_id] = the raw object (the entire EOC item)
    """
    if not isinstance(json_data, list):
        print("Warning: top-level JSON is not a list. Attempting to parse anyway.")
        return {}

    eoc_dict = {}
    for obj in json_data:
        if isinstance(obj, dict) and obj.get("type") == "effect_on_condition":
            eoc_id = obj.get("id")
            if eoc_id:
                eoc_dict[eoc_id] = obj
    return eoc_dict

def add_recurrence_and_deactivate(eoc_dict, target_id, recurrence_val=3600, var_name="sflesh_infected", var_value="yes"):
    """
    Inject or override:
      "recurrence": <recurrence_val>
      "deactivate_condition": { "compare_string": [ { "u_val": var_name }, var_value ] }

    in the EOC with ID == target_id.
    """
    if target_id in eoc_dict:
        eoc_obj = eoc_dict[target_id]
        eoc_obj["recurrence"] = recurrence_val
        eoc_obj["deactivate_condition"] = {
            "compare_string": [
                { "u_val": var_name },
                var_value
            ]
        }
    else:
        print(f"Warning: EOC id='{target_id}' not found in the dictionary.")

def rebuild_full_json(json_data, eoc_dict_modified):
    """
    Rebuild top-level JSON array to include modified EOCs properly.
    Ensures nested inline EOCs are preserved correctly.
    """
    if not isinstance(json_data, list):
        return json_data

    new_list = []
    for obj in json_data:
        if isinstance(obj, dict) and obj.get("type") == "effect_on_condition":
            the_id = obj.get("id")
            if the_id and the_id in eoc_dict_modified:
                # Instead of directly overwriting, copy fields carefully
                original_obj = dict(obj)  # Start from original object to preserve nested structures
                modified_obj = eoc_dict_modified[the_id]

                # Update recurrence and deactivate_condition if present
                for field in ["recurrence", "deactivate_condition"]:
                    if field in modified_obj:
                        original_obj[field] = modified_obj[field]

                # Keep existing effect field intact
                original_obj["effect"] = modified_obj.get("effect", original_obj.get("effect", []))

                new_list.append(original_obj)
            else:
                new_list.append(obj)
        else:
            new_list.append(obj)
    return new_list

def main(input_path, output_path):
    data = load_json(input_path)

    # Gather EOC dict
    eoc_dict = gather_eoc_dict(data)

    # Add recurrence and deactivate logic to your specific EOC
    add_recurrence_and_deactivate(
        eoc_dict,
        target_id="eoc_secro_mon_flesh_infect",
        recurrence_val=3600,
        var_name="sflesh_infected",
        var_value="yes"
    )

    # Rebuild JSON (use the corrected rebuild_full_json function)
    final_data = rebuild_full_json(data, eoc_dict)

    # Save modified JSON
    save_json(final_data, output_path)

    print(f"Added recurrence and deactivate condition to 'eoc_secro_mon_flesh_infect'.")
    print(f"Saved modified data to {output_path}.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input.json> <output.json>")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2]
    main(inp, out)
