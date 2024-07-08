# %%
import os
import json
import tempfile
import subprocess

# %%
template = '''def get_values(*names):
    import json
    _all_values = json.loads("""{data}""")
    return [_all_values[n] for n in names]
'''

# %%
for subdir, _, files in os.walk('../protocols'):
    py_file = [file for file in files if file.endswith('.py')]
    if not py_file:
        continue
    if len(py_file) != 1:
        continue
    
    py_file = py_file[0]
    save_file_name = py_file[:-3]

    # Handle fields.json
    with open(os.path.join(subdir, 'fields.json'), 'r') as f:
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
                   f"--human-json-output=../datasets/{save_file_name}.json",
                   f"{temp_filename}"]

        # Check if subdir/labware exists
        labware_path = os.path.join(subdir, 'labware')
        if os.path.isdir(labware_path):
            command.append(labware_path)

        try:
            print(command)
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(result.stdout)  # Optionally print the stdout to see the results
        except Exception as e:
            print(e)
            print("Command failed with return code:", e.returncode if hasattr(e, 'returncode') else 'N/A')
            print("Error output:", e.stderr if hasattr(e, 'stderr') else 'N/A')
            break

    # break

    # has_valid_file = any(file.endswith('.py') or file.endswith('.md') for file in files)
    # if not has_valid_file:
    #     continue
    
    # py_file = [file for file in files if file.endswith('.py')][0]
    
    # command = ["python", "-m", "opentrons.cli", "analyze", "--human-json-output=../datasets/demo-analyse.json", f"{subdir}/{py_file}"]
    
    # try:
    #     print(subdir)
    #     result = subprocess.run(command, capture_output=True, text=True, check=True)
    # except Exception as e:
    #     print(e)
    #     print("Command failed with return code:", e.returncode)
    #     print("Error output:", e.stderr)
    #     break
    
    # break
    
    
    # # Look for a Markdown (.md) file in the current subdirectory
    # md_files = [file for file in files if file.endswith('.md')]
    
    # for md_file in md_files:
    #     md_file_path = os.path.join(subdir, md_file)

    #     # Read and print the content of the Markdown file
    #     with open(md_file_path, 'r') as f:
    #         content = f.read()

# %%



