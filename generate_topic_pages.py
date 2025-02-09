#!/usr/bin/env python3

# Standard Library
import os
import re
import glob
import time

# PIP3 modules
import yaml

# Local
import bb_text_to_html
import llm_generate_problem_set_title

#==============

BASE_DIR: str = "./docs"
MKDOCS_CONFIG: str = "mkdocs.yml"

#==============

def get_topic_title(folder_path: str, topic_number: int) -> str:
	"""Retrieve the topic title from mkdocs.yml.

	Args:
		folder_path (str): The path to the topic folder.
		topic_number (int): A topic number (currently unused).

	Returns:
		str: The title of the topic, or 'Untitled Topic' if not found.

	Raises:
		FileNotFoundError: If the mkdocs.yml file does not exist.
		ValueError: If no title is found for the given folder path.
	"""
	# Check if the config file exists
	if not os.path.exists(MKDOCS_CONFIG):
		raise FileNotFoundError(f"Config file '{MKDOCS_CONFIG}' not found.")

	# Get the relative path of the folder
	relative_path = os.path.relpath(folder_path, BASE_DIR)

	# Load the navigation structure from mkdocs.yml
	with open(MKDOCS_CONFIG, "r") as file:
		config = yaml.safe_load(file)

	# Traverse the navigation structure to find the topic title
	for section in config.get("nav", []):
		for key, subsections in section.items():
			for subsection in subsections:
				if isinstance(subsection, dict):
					for title, index_file in subsection.items():
						# Check if the folder path matches
						if relative_path in index_file:
							return title

	# If no matching title is found, raise an error
	raise ValueError(f"No topic title found for folder path: {folder_path}")

#==============

def get_topic_description(parent_folder: str, relative_topic_name: str) -> str:
	"""Retrieve the description from the parent folder's index.md file.

	Args:
		parent_folder (str): The path to the parent folder containing index.md.
		relative_topic_name (str): The name of the topic for which to find the description.

	Returns:
		str: The description found in the index.md file.

	Raises:
		ValueError: If the index.md file does not exist or no matching description is found.
	"""
	# Path to the index.md file
	index_md_path = os.path.join(parent_folder, "index.md")
	print(f"Parent Index file: {index_md_path}")

	if not os.path.exists(index_md_path):
		raise ValueError(f"No index.md file found in the folder: {parent_folder}")

	# Normalize the search path (topic folder with "index.md")
	search_path = os.path.normpath(os.path.join(relative_topic_name, "index.md"))
	print(f"Search path: {search_path}")

	#Sample
	"""
	1. [The Molecular Design of Life](topic01/index.md)
		- Molecular design of life, major elements, and biomacromolecules.
	"""

	# Read the file and find the line after the topic path
	with open(index_md_path, "r") as file:
		for line in file:
			sline = line.strip()
			# Check if the current line contains the normalized topic path
			if search_path in os.path.normpath(sline):
				# Get the next line, which should contain the description
				next_line = file.readline().strip()
				description = re.sub(r"^[\-\s]*", "", next_line)
				if description:
					return description

	# If no matching description is found
	raise ValueError(f"No description found for topic: {relative_topic_name}")

#==============

def get_problem_set_title(bbq_file: str) -> str:
	"""
	Extracts or generates the title for a problem set based on the provided file path.

	Args:
		bbq_file (str): The full path to the problem set file.

	Returns:
		str: The title of the problem set.
	"""
	# Normalize and obtain the directory path of the file
	bbq_file_path = os.path.normpath(bbq_file)
	dir_path = os.path.dirname(bbq_file_path)

	# Define the path for the YAML file containing problem set titles
	problem_set_title_yaml = os.path.join(dir_path, 'problem_set_titles.yml')

	# Check if the YAML file exists
	if os.path.isfile(problem_set_title_yaml):
		# Load the YAML data if the file exists
		with open(problem_set_title_yaml, 'r') as problem_set_title_file_pointer:
			problem_set_title_data = yaml.safe_load(problem_set_title_file_pointer)
	else:
		# Initialize an empty dictionary if the file doesn't exist
		problem_set_title_data = {}

	# Extract the base file name from the input path
	bbq_file_basename = os.path.basename(bbq_file)

	# If the file's title is already in the YAML data, return it
	if bbq_file_basename in problem_set_title_data:
		return problem_set_title_data[bbq_file_basename]

	# Generate a new title using an external module function
	problem_set_title = llm_generate_problem_set_title.get_problem_title_from_file(bbq_file)

	# Update the YAML data with the newly generated title and a timestamp of the edit
	problem_set_title_data[bbq_file_basename] = problem_set_title
	problem_set_title_data['last edit'] = time.asctime()

	# Write the updated data back to the YAML file
	with open(problem_set_title_yaml, "w") as problem_set_title_file_pointer:
		yaml.dump(problem_set_title_data, problem_set_title_file_pointer)

	# Return the newly generated problem set title
	return problem_set_title

#==============

def update_index_md(topic_folder: str, bbq_files: list) -> None:
	"""Update or create the index.md file for the topic.

	Args:
		topic_folder (str): The path to the topic folder.
		subtitle (str): The subtitle for the topic.
		bbq_files (list[str]): List of BBQ file paths to process.
	"""
	# Get subtitle from the parent folder's index.md
	# Normalize the folder path to handle trailing slashes
	normalized_path = os.path.normpath(topic_folder)

	# Extract the last directory name (e.g., "topic09")
	relative_topic_name = os.path.basename(normalized_path)
	relative_path = os.path.relpath(normalized_path, BASE_DIR)

	topic_number = int(re.search('topic([0-9]+)', relative_topic_name).groups()[0])
	print(f"Topic Number: {topic_number}")

	title = get_topic_title(topic_folder, topic_number)
	print(f"Page Title: {title}")

	parent_folder = os.path.dirname(topic_folder)
	if 'topic' in parent_folder:
		raise ValueError(f"topic should not be in parent_folder {parent_folder}")
	description = get_topic_description(parent_folder, relative_topic_name)
	print(f"Page description: {description}")

	index_md_path = os.path.join(topic_folder, "index.md")
	print(f'writing to {index_md_path}')
	with open(index_md_path, "w") as index_md:

		index_md.write(f"# {title}\n\n")
		index_md.write(f"{description}\n\n")

		bbq_files.sort()
		for bbq_file in bbq_files:
			print('-' * 50)
			# Extract the base file name from the input path
			bbq_file_basename = os.path.basename(bbq_file)
			# Convert the text file to HTML
			print(f'  BBQ file {bbq_file}')
			html_file = bb_text_to_html.get_output_filename(bbq_file)
			html_file_path = os.path.join(normalized_path, html_file)
			bb_text_to_html.convert_text_to_html(bbq_file, html_file_path)

			# Generate the problem set title using the LLM
			problem_set_title = get_problem_set_title(bbq_file)
			print(f"  Problem set title: {problem_set_title}")

			# Add content to the index.md file
			index_md.write(f"## {problem_set_title}\n\n")
			download_msg = f"Download the {bbq_file_basename} file for Blackboard Upload"
			markdown_link = f"[{download_msg}]({bbq_file_basename})\n\n"
			a_href = f"<a id='raw-url' href='{bbq_file_basename}' download>{download_msg}</a>\n\n"
			index_md.write(a_href)
			index_md.write("<details>\n")
			index_md.write(f"  <summary>\"Click to show example problem on {problem_set_title}\"</summary>\n")
			index_md.write(f"  {{% include \"{os.path.relpath(html_file_path, BASE_DIR)}\" %}}\n\n")
			index_md.write("<br/></details>\n")

#==============

def main():
	"""Traverse the topic folders and generate pages.

	Raises:
		FileNotFoundError: If the base directory does not exist.
	"""
	if not os.path.exists(BASE_DIR):
		raise FileNotFoundError(f"Base directory '{BASE_DIR}' not found.")

	search_text = os.path.join(BASE_DIR, "*/topic??")
	print(f"Search text: {search_text}")
	all_topic_folders = glob.glob(os.path.join(BASE_DIR, "*/topic??/"))
	all_topic_folders.sort()
	print(f"Found {len(all_topic_folders)} topic folders to parse")


	for topic_folder in all_topic_folders:
		print("\n\n\n################################")
		topic_folder = os.path.normpath(topic_folder)
		# Skip the base directory itself and non-topic folders
		if topic_folder == BASE_DIR:
			continue

		if not 'topic' in topic_folder:
			continue

		print(f"Current folder: {topic_folder}")
		# Check for BBQ files
		# glob is probably more efficient
		bbq_files = glob.glob(os.path.join(topic_folder, "bbq-*-questions.txt"))
		if not bbq_files:
			continue
		print(f"Found {len(bbq_files)} bbq files in topic folder: {topic_folder}")

		# Update the index.md file for the topic
		update_index_md(topic_folder, bbq_files)

#==============

if __name__ == "__main__":
	main()
