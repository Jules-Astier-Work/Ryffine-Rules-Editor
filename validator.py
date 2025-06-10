"""
DITA RNG Validator using XML Catalog

This script validates DITA files against Ryffine RNG schemas using a catalog.xml file.
"""
from dataclasses import dataclass
import os
from typing import List
import re
from pathlib import Path
from xml.dom import minidom
import pandas as pd

LLM_FEEDBACK_PROMPT = """
You are an Expert at writing RyffineDITA, a specialized version of DITA.
Here is a report of a previous failed attpemt to write RyffineDITA.
There is a comprehensive list of rules that were violated.
Rewrite the RyffineDITA content and fix the errors raised.
IMPORTANT: Output ONLY the new RyffineDITA content.
"""


def prettify_xml(xml_string):
	dom = minidom.parseString(xml_string)
	pretty = dom.toprettyxml(indent="  ")
	pretty = pretty.replace('<?xml version="1.0" ?>\n', '')
	return re.sub(r'\n\s*\n', '\n', pretty).strip()

@dataclass
class JingError:
	root_name: str | None = None
	content: str | None = None
	error_rules: str | pd.DataFrame | None = None
	parent_element: str | None = None
	child_element: str | List[str] | None = None
	applicable_to: List[str] | None = None
	is_attribute_error: bool = False
	error: str | None = None
	line: str | None = None
	char: str | None = None

	@staticmethod
	def parse_list(list_str):
		values = re.findall(r'"([^"]+)"', list_str)
	
		if not values:
			# Try splitting by "or" for unquoted values
			values = [v.strip() for v in list_str.split(' or ')]

		return values

	def split_on_line_char(self):
		lines = self.content.split("\n")
		pre_split = lines[:self.line] + [lines[self.line][:self.char]]
		post_split = [lines[self.line][self.char:]] + lines[self.line + 1:]
		return "\n".join(pre_split), "\n".join(post_split)
	
	def get_last_unclosed_tag(self, content):
		pattern = r'<([a-zA-Z][\w-]*)\b[^/>]*(?<!/)>(?![\s\S]*?<\/\1>)'
		
		# Use DOTALL flag to match across newlines
		matches = list(re.finditer(pattern, content, re.DOTALL))
		if matches:
			return matches[-1].group(1)

	def get_last_opened_tag(self, content):
		pattern = r'<(.+?)\s'
		
		# Use DOTALL flag to match across newlines
		# print(content)
		matches = list(re.finditer(pattern, content, re.DOTALL))
		# print(matches)
		if matches:
			return matches[-1].group(1)

	def parse_error(self, error_str, content):
		self.content = content
		root_pattern = r'(?:<\?xml[^>]*\?>\s*)?<(\w+)'
		root_match: re.Match | None = re.match(root_pattern, content)
		self.root_name = root_match.group(1)

		error_pattern = r'^(?P<file>.+):(?P<line>\d+):(?P<char>\d+): error: (?P<error>.+)$'
		error_match: re.Match | None = re.match(error_pattern, error_str)
		if error_match is not None:
			groups = error_match.groupdict()
			self.error = groups["error"]
			self.line = int(groups["line"]) - 1
			self.char = int(groups["char"]) - 2
			
			# Pattern 1: Element not allowed
			pattern = r'element "([^"]+)" not allowed (?:here|anywhere)(?:; expected element (.+))?'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["content_rule", "containment_rule", "mixed_content_rule"]
				if match.group(2):
					# Parse expected elements
					expected_str = match.group(2)
					self.child_element = self.parse_list(expected_str)

			# Pattern 1: Element not allowed
			pattern = r'element "([^"]+)" not allowed yet(?:; expected element (.+))?'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["order_rule"]
				if match.group(2):
					# Parse expected elements
					expected_str = match.group(2)
					self.child_element = self.parse_list(expected_str)
			
			# Pattern 2: Missing required element
			pattern = r'element "(?P<parent_element>[^"]+)" incomplete; missing required element "([^"]+)"'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["content_rule", "containment_rule", "mixed_content_rule"]
				self.parent_element = match.group("parent_element")
				self.child_element = match.group(1)
			
			# Pattern 3: Attribute not allowed
			pattern = r'attribute "([^"]+)" not allowed here'
			match = re.match(pattern, self.error)
			if match:
				self.is_attribute_error = True
				pass

			# Pattern 3: Attribute not allowed
			pattern = r'found attribute "([^"]+)", but no attributes allowed here'
			match = re.match(pattern, self.error)
			if match:
				self.is_attribute_error = True
				pass
			
			# Pattern 4: Missing required attribute
			pattern = r'element "(?P<parent_element>[^"]+)" missing required attribute "([^"]+)"'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["element_uses_attribute_set_rule", "attribute_rule"]
				self.parent_element = match.group("parent_element")
				self.child_element = match.group(1)
			
			# Pattern 5: Invalid attribute value
			pattern = r'value of attribute "(?P<child_element>[^"]+)" is invalid; must be (.+)'
			match = re.match(pattern, self.error)
			if match:
				self.is_attribute_error = True
				self.applicable_to = ["element_uses_attribute_set_rule", "attribute_rule"]
				self.child_element = match.group("child_element")
			
			# Pattern 6: Text not allowed
			pattern = r'text not allowed here'
			match = re.match(pattern, self.error)
			if match:
				pass
			
			# Pattern 7: Element not allowed to have content
			pattern = r'element "(?P<parent_element>[^"]+)" not allowed to have content'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["empty_rule"]
				self.parent_element = match.group("parent_element")

			# Pattern 8: Pattern mismatch
			pattern = r'character content of element "(?P<parent_element>[^"]+)" invalid; must match pattern "([^"]+)"'
			match = re.match(pattern, self.error)
			if match:
				self.parent_element = match.group("parent_element")

			# Pattern 9: Expected one of (choice)
			pattern = r'element "(?P<parent_element>[^"]+)" incomplete; expected one of \((.+)\)'
			match = re.match(pattern, self.error)
			if match:
				self.applicable_to = ["content_rule", "containment_rule", "mixed_content_rule"]
				self.parent_element = match.group("parent_element")
				if match.group(1):
					# Parse expected elements
					expected_str = match.group(1)
					self.child_element = self.parse_list(expected_str)
			
			# Pattern 10: Datatype validation
			pattern = r'character content of element "(?P<parent_element>[^"]+)" invalid; not a valid "([^"]+)"'
			match = re.match(pattern, self.error)
			if match:
				self.parent_element = match.group("parent_element")
			
			# Pattern 11: IDREF without matching ID
			pattern = r'IDREF "([^"]+)" without matching ID'
			match = re.match(pattern, self.error)
			if match:
				pass
			
			# Pattern 12: Namespace error
			pattern = r'element "(?P<child_element>[^"]+)" from namespace "([^"]+)" not allowed in this context'
			match = re.match(pattern, self.error)
			if match:
				pass
			

			if self.parent_element is None:
				pre, post = self.split_on_line_char()
				if self.is_attribute_error:
					self.parent_element = self.get_last_opened_tag(pre)
				else:
					self.parent_element = self.get_last_unclosed_tag(pre)

	def get_error_text(self):
		if isinstance(self.error_rules, str):
			return [self.error]
		else:
			return self.error_rules['rule'].tolist()

class RyffineDITAContent:
	def __init__(self, errors: List[JingError], content: str):
		self.errors = errors
		self.content = self.add_line_number_context(content)

	@staticmethod
	def add_line_number_context(xml_string: str):
		def pad_line_number(line_number, number_of_lines):
			number_str = str(line_number)
			padding = "0" * (len(str(number_of_lines)) - len(number_str))
			return padding + number_str
		lines = xml_string.split("\n")
		lines = [
			f"{pad_line_number(i, len(lines))} | {line}"
			for i, line in enumerate(lines, 1)
		]
		return "\n".join(lines)

	def get_general_definitions(self):
		general_errors = [
			e for e in self.errors
			if isinstance(e.error_rules, str)
		]

		return {
			e.parent_element: prettify_xml(e.error_rules)
			for e in general_errors	
		}
	
	def get_line_errors(self):
		line_errors = {}
		for error in self.errors:
			if line_errors.get(error.line + 1) is None:
				line_errors[error.line + 1] = []
			line_errors[error.line + 1].extend(error.get_error_text())
		return line_errors

	@staticmethod
	def get_custom_errors(error: JingError):
		if isinstance(error.error_rules, str):
			return [f"{error.error} ---> Refer to definition for \"{error.parent_element}\"  found below"]
		else:
			return error.error_rules["rule"].tolist()
		 
	def get_line_report(self, line_number, errors: List[JingError]):
		return f"""
- Line {line_number}:
	{"\n	".join([error for error in errors])}"""

	def build_llm_report(self):
		# Get unique definitions
		general_defintions = self.get_general_definitions()
		
		# Group by line
		line_errors = self.get_line_errors()

		return f"""
{LLM_FEEDBACK_PROMPT}
Generated DITA Content:
{self.content}
-----------------------------------------------
Errors:
{"\n".join([self.get_line_report(k, v) for k, v in line_errors.items()])}
-----------------------------------------------
Definitions:

{"\n\n".join(general_defintions.values())}
"""

class RyffineDITAValidator:
	# element_to_schema = {
	#     'concept': 'consolidated/ryffineConcept.rng',
	#     'task': 'consolidated/ryffineTask.rng',
	#     'reference': 'consolidated/ryffineReference.rng',
	#     'troubleshooting': 'consolidated/ryffineTroubleshooting.rng',
	#     'glossentry': 'consolidated/ryffineGlossentry.rng',
	#     'learningOverview': 'consolidated/ryffineLearningOverview.rng',
	#     'map': 'consolidated/ryffineMap.rng',
	#     'bookmap': 'consolidated/ryffineBookmap.rng'
	# }

	def __init__(self, rules_df: pd.DataFrame = None, ryffine_dita_path="ryffine_dita"):
		self.ryffine_dita_path = Path(ryffine_dita_path)
		self.rules_df = rules_df or pd.read_csv(self.ryffine_dita_path / "rules/all_new.csv")
		self.element_to_schema = {
			self.file_name_to_root_name(f): f"consolidated/{f}"
			for f in os.listdir(self.ryffine_dita_path / "consolidated")
		}
		
	@staticmethod
	def file_name_to_root_name(file_name: str):
		root_name = file_name.replace("ryffine", "").replace(".rng", "")
		return root_name[0].lower() + root_name[1:]

	def validate_content(self, content):
		import tempfile
		import subprocess
		import os
		import xml.etree.ElementTree as ET

		content = prettify_xml(content)
		root = ET.fromstring(content)
		root_name = root.tag
		
		if root_name in self.element_to_schema:
			schema_path = self.ryffine_dita_path / self.element_to_schema[root_name]
			if not schema_path.exists():
				raise ValueError("No schema")
			
			with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
				temp_file.write(content)
				temp_file.flush()

				cmd = ["java", "-jar", "jing.jar", schema_path, temp_file.name]

				try:
					result = subprocess.run(cmd, capture_output=True, text=True, check=False)
					
					# Get stderr (where jing outputs errors) and split into lines
					error_lines = result.stderr.strip().split('\n') if result.stderr.strip() else []
					# Get stdout and split into lines  
					output_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
					
					# Combine both (jing typically outputs to stderr)
					all_lines = output_lines + error_lines
					
					# Filter out empty lines
					errors = [line for line in all_lines if line.strip()]
					jing_errors = []
					for error in errors:
						jing_error = JingError()
						jing_error.parse_error(error, content)
						jing_error.error_rules = self.get_error_details(jing_error)
						jing_errors.append(jing_error)

					return RyffineDITAContent(jing_errors, content)
					
				except FileNotFoundError:
					raise
				
				finally:
					os.unlink(temp_file.name)

	def get_error_details(self, error: JingError) -> str | pd.DataFrame:
		if error.applicable_to:
			# Filter for rules relating to the parent element
			error_rules_df = self.rules_df[self.rules_df["rule_element"] == f"<define name=\"{error.parent_element}\">"]
			# Filter for rule types linked to that error
			error_rules_df = error_rules_df[error_rules_df["rule_type"].apply(lambda x: self.filter_on_rule_type(x, error.applicable_to))]
			# TODO: Filter for child elements in the rule/error
			if len(error_rules_df) == 0:
				return self.get_defintion(error.parent_element, error.root_name)
			return error_rules_df
		else:
			return self.get_defintion(error.parent_element, error.root_name)

	def get_defintion(self, tag_name, root_name):
		rng_file_path = self.ryffine_dita_path / self.element_to_schema[root_name]
		with open(rng_file_path, "r") as f:
			rng_file = f.read()
		# Find definition
		escaped_tag_name = re.escape(tag_name)
		pattern = rf'<(define)\s+name="{escaped_tag_name}">(.*?)</\1>'

		# Use DOTALL flag to match across newlines
		match = re.search(pattern, rng_file, re.DOTALL)

		if match:
			return match.group(0).strip()
		return None

	@staticmethod
	def filter_on_rule_type(rule_type: str, applicable_to: List[str]):
		if rule_type is not None and applicable_to is not None:
			return rule_type in applicable_to
		return True
