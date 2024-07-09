import os
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
from tqdm import tqdm

# Template for the get_values function to be inserted into the python scripts
template = '''def get_values(*names):
    import json
    _all_values = json.loads("""{data}""")
    return [_all_values[n] for n in names]
'''

def read_fields_json(fields_json_path):
    """Reads and processes the fields.json file."""
    with open(fields_json_path, 'r') as f:
        s = f.read()
        data = json.loads(s)
        processed_data = {}
        for item in data:
            value = item['default'] if item['type'] != 'dropDown' else item['options'][0]['value']
            if isinstance(value, str):
                value = value.replace('\n', '\\n')
            processed_data[item['name']] = value
        return json.dumps(processed_data)

def insert_template_into_script(template, script_contents):
    """Inserts the template at the appropriate location in the script."""
    # Find the index of the line where 'metadata' is declared
    metadata_index = next(i for i, line in enumerate(script_contents) if line.strip().startswith('metadata'))
    # Insert the filled template before this line
    script_contents.insert(metadata_index, template + "\n")
    return script_contents

def process_file(subdir, py_file, counter_dict, total):
    """Processes a single .py file and runs the necessary command."""
    save_file_name = py_file[:-3]

    # Handle fields.json
    fields_json_path = os.path.join(subdir, 'fields.json')
    template_content = ''
    if os.path.exists(fields_json_path):
        template_content = template.replace('{data}', read_fields_json(fields_json_path))

    # Handle .py
    with open(os.path.join(subdir, py_file), 'r') as f:
        script_contents = f.readlines()
        script_contents = insert_template_into_script(template_content, script_contents)

    # Save the modified script to the ../datasets/code directory
    output_dir = os.path.join('..', 'datasets', 'code')
    os.makedirs(output_dir, exist_ok=True)
    output_script_path = os.path.join(output_dir, f"{save_file_name}.py")
    with open(output_script_path, 'w') as f:
        f.writelines(script_contents)

    # Prepare the command
    os.makedirs('../datasets/json', exist_ok=True)
    command = ["python", "-m", "opentrons.cli", "analyze",
               f"--json-output=../datasets/json/{save_file_name}.json",
               output_script_path]

    # Check if subdir/labware exists
    labware_path = os.path.join(subdir, 'labware')
    if os.path.isdir(labware_path):
        command.append(labware_path)

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        counter_dict['value'] += 1
        return f"Processed {counter_dict['value']}/{total}: {save_file_name}"
    except Exception as e:
        return f"Error processing {save_file_name}: {str(e)}"

def main():
    tasks = []
    manager = Manager()
    counter_dict = manager.dict()
    counter_dict['value'] = 0

    # First, count total number of files
    total_files = sum(1 for subdir, _, files in os.walk('../protocols')
                      for file in files if file.endswith('.py'))

    with ProcessPoolExecutor() as executor:
        for subdir, _, files in os.walk('../protocols'):
            py_files = [file for file in files if file.endswith('.py')]
            if not py_files or len(py_files) != 1:
                continue
            
            py_file = py_files[0]
            tasks.append(executor.submit(process_file, subdir, py_file, counter_dict, total_files))

        with tqdm(total=total_files, desc="Processing files") as pbar:
            for future in as_completed(tasks):
                result = future.result()
                tqdm.write(result)
                pbar.update(1)

    print(f"Processed {counter_dict['value']}/{total_files} files.")

if __name__ == "__main__":
    main()