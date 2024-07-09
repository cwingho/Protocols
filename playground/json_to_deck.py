import os
import json
from tqdm import tqdm

def sort_key(k):
    """Return a tuple for sorting by numeric and alphabetic keys."""
    return (0, int(k)) if k.isdigit() else (1, k)

def get_module_name(module_id, modules):
    """Return the module name matching the given ID, or None if not found."""
    for module in modules:
        if module['id'] == module_id:
            return module['model']
    return None

def process_file(file_path, output_dir):
    """Process a single JSON file to extract and sort deck information."""
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
        except Exception as e:
            print(file_path)
            raise
        labware = data['labware']
        modules = data['modules']
    
    deck = {module['location']['slotName']: module['model'] for module in modules}
    
    for lw in labware:
        location = lw['location']
        if 'slotName' in location:
            deck[location['slotName']] = lw['loadName']
        elif 'moduleId' in location:
            module_name = get_module_name(location['moduleId'], modules)
            deck[module_name] = lw['loadName']
    
    sorted_deck = {k: deck[k] for k in sorted(deck.keys(), key=sort_key)}
    
    output_path = os.path.join(output_dir, os.path.basename(file_path))
    with open(output_path, 'w') as file:
        json.dump(sorted_deck, file, indent=4)

def main():
    input_folder = '../datasets/json'
    output_folder = '../datasets/deck'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    files_to_process = []
    for root, _, files in os.walk(input_folder):
        for file in files:
            files_to_process.append(os.path.join(root, file))
    
    for file_path in tqdm(files_to_process, desc="Processing files"):
        process_file(file_path, output_folder)

if __name__ == "__main__":
    main()