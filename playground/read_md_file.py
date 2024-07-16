
# %autoawait asyncio

import re
import os
import glob
import aiohttp
import httpx
import asyncio
import nest_asyncio
from tqdm.asyncio import tqdm

nest_asyncio.apply()

def remove_urls(text):
    # Pattern to match Markdown links and remove the URL part
    markdown_link_pattern = r'\[([^\]]+)\]\(\S+\)'
    return re.sub(markdown_link_pattern, r'[\1]', text)

def filter_sections(lines, sections_keywords):
    in_section = False
    filtered_lines = []

    for line in lines:
        # Check if the line is a header
        header_match = re.match(r'^(#+)\s*(.*)', line)
        if header_match:
            current_header_level = len(header_match.group(1))
            header_text = header_match.group(2).strip()
            # Check if the header matches any of the keywords
            if any(keyword in header_text for keyword in sections_keywords):
                in_section = True
                section_to_drop_level = current_header_level
                continue
            # If we are in a section to drop and encounter a header of the same or higher level, stop dropping
            if in_section and current_header_level <= section_to_drop_level:
                in_section = False

        # If not in a section to drop, add the line to filtered_lines
        if not in_section:
            filtered_lines.append(line)

    return filtered_lines

def preprocess(dir):
    # Read the content of the Markdown file
    with open(dir, "r") as file:
        lines = file.readlines()

    # Define the keywords for sections to drop content from
    sections_to_drop = ["Process", "Additional Notes", "Author", "Internal", "Categories", 'Deck Setup', 'Reagent Setup','Links']

    # Filter the content inside the specified sections
    filtered_lines = filter_sections(lines, sections_to_drop)

    # Remove URLs from the filtered content
    filtered_lines = [remove_urls(line) for line in filtered_lines]

    # Join and print the filtered content
    return ''.join(filtered_lines).replace('\n\n','\n')


cmd = []
for dir in glob.glob('../protocols/*/'):
    readme_path = os.path.join(dir, 'README.md')
    if os.path.isfile(readme_path):
        cmd.append(preprocess(readme_path))


async def get_conv_id(session):
    url = "http://localhost:8000/llm/chat/new"
    headers = {
        'Content-Type': 'application/json',
        'Lang': 'en'
    }

    async with session.post(url, headers=headers, json={}) as response:
        response_json = await response.json()
        return response_json['data']

async def gen_cmd(session, conv_id, cmd):
    url = f"http://localhost:8000/llm/gen_cmd/{conv_id}"
    timeout = httpx.Timeout(None)  # Set a higher read timeout

    async with httpx.AsyncClient(timeout=timeout) as client:
        data = {"data": cmd}
        async with client.stream("POST", url, json=data) as response:
            async for chunk in response.aiter_text():
                pass
    return True

async def handle_request(semaphore, session, cmd):
    async with semaphore:
        try:
            conv_id = await get_conv_id(session)
            result = await gen_cmd(session, conv_id, cmd)
        except Exception as e:
            print(f'failed with conv_id: {conv_id}. Error: {e}')
            return False
        return result

async def main(commands):
    semaphore = asyncio.Semaphore(4)  # Limit to 10 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [handle_request(semaphore, session, cmd) for cmd in commands]
        results = []
        for f in tqdm.as_completed(tasks, total=len(tasks)):
            result = await f
            results.append(result)
    return results

results = asyncio.run(main(cmd))





