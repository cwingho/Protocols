import os
import json
import tempfile
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
from tqdm import tqdm

template = '''def get_values(*names):
    import json
    _all_values = json.loads("""{data}""")
    return [_all_values[n] for n in names]
'''

def process_file(subdir, py_file, counter_dict, total):
    save_file_name = py_file[:-3]

    # Handle fields.json
    fields_json_path = os.path.join(subdir, 'fields.json')
    t = ''
    if os.path.exists(fields_json_path):
        with open(fields_json_path, 'r') as f:
            s = f.read()
            data = json.loads(s)
            data = {i['name']: (i['default'] if i['type'] != 'dropDown' else i['options'][0]['value']) for i in data}
            data = json.dumps(data)
            t = template.replace('{data}', data)

    # Handle .py
    with open(os.path.join(subdir, py_file), 'r') as f:
        script_contents = f.readlines()

        # Find the index of the line where 'metadata' is declared
        metadata_index = next(i for i, line in enumerate(script_contents) if line.strip().startswith('metadata'))

        # Insert the filled template before this line
        script_contents.insert(metadata_index, t + "\n")

        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.py') as temp_file:
            temp_file.writelines(script_contents)
            temp_filename = temp_file.name  # Store the name for further processing

        # Prepare the command
        command = ["python", "-m", "opentrons.cli", "analyze",
                   f"--json-output=../datasets/{save_file_name}.json",
                   f"{temp_filename}"]

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