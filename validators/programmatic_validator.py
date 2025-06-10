from dataclasses import dataclass
from typing import List
import xml.etree.ElementTree as ET
import re

from validators.utils import clean_dita, prettify_xml

@dataclass
class ProgrammaticRyffineDITAError:
	line: int
	error: str

class ProgrammaticValidator:
	def __init__(self):
		self.programattic_checks = {
			"<title> length is {title_length} characters but the max length is {max_length}.": self.check_title_length,
			"<shortdesc> is {shortdesc_word_count} words but the max length is {max_word_count}.": self.check_shortdesc_word_count,
			"\"{parent_element}\" cannot contain <indexterm> mid-sentence.": self.check_index_term_placement
		}
	
	# Util methods
	@staticmethod
	def find_elements_with_line_numbers(content: str, tag_name: str):
		"""Find all instances of an XML element and return with their line numbers and content."""
		# Pattern to match opening tag, content, and closing tag
		pattern = rf'<{tag_name}(?:\s[^>]*)?>(.*?)</{tag_name}>'
		
		matches = []
		for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
			# Calculate line number from character position
			line_num = content[:match.start()].count('\n') + 1
			content_text = match.group(1).strip()
			matches.append((line_num, content_text, match))
		
		return matches

	@staticmethod
	def find_all_elements(root, elem: str | List[str]):
		"""Find all matching elements."""
		if isinstance(elem, str):
			elem = [elem]
		elements = []
		for element in root.iter():
			if element.tag.lower() in elem:
				elements.append(element)
		return elements

	@staticmethod
	def find_first_elem(root, elem: str | List[str]):
		if isinstance(elem, str):
			elem = [elem]
		for element in root.iter():
			if element.tag.lower() in elem:
				return element

	@staticmethod
	def find_parent_element(content, indexterm_start_pos):
		"""Find the parent element that contains the indexterm at the given position."""
		# Look backwards from the indexterm position to find the most recent opening tag
		content_before = content[:indexterm_start_pos]
		
		# Find all opening tags before this position (in reverse order)
		opening_tags = []
		closing_tags = []
		
		# Pattern for opening tags: <tagname> or <tagname attributes>
		opening_pattern = r'<([a-zA-Z][a-zA-Z0-9\-]*)(?:\s[^>]*)?>'
		# Pattern for closing tags: </tagname>
		closing_pattern = r'</([a-zA-Z][a-zA-Z0-9\-]*)'
		
		# Find all tags before the indexterm position
		for match in re.finditer(opening_pattern, content_before):
			opening_tags.append((match.group(1), match.start()))
		
		for match in re.finditer(closing_pattern, content_before):
			closing_tags.append((match.group(1), match.start()))
		
		# Sort all tags by position
		all_tags = [(tag, pos, 'open') for tag, pos in opening_tags] + [(tag, pos, 'close') for tag, pos in closing_tags]
		all_tags.sort(key=lambda x: x[1])
		
		# Find the most recent unclosed opening tag
		tag_stack = []
		for tag_name, pos, tag_type in all_tags:
			if tag_type == 'open':
				tag_stack.append(tag_name)
			elif tag_type == 'close' and tag_stack and tag_stack[-1] == tag_name:
				tag_stack.pop()
		
		# The last item in the stack is our parent element
		return tag_stack[-1] if tag_stack else "unknown"

	# Programmatic Checks
	def check_title_length(self, error_str, content, max_length=70):
		errors = []
		
		# Find all title elements with their line numbers using regex
		title_matches = self.find_elements_with_line_numbers(content, 'title')
		
		for line_num, title_text, match in title_matches:
			if title_text:
				title_length = len(title_text)
				if title_length > max_length:
					errors.append(ProgrammaticRyffineDITAError(
						line_num,
						error_str.format(
							title_length=title_length,
							max_length=max_length
						)
					))
		
		return errors
				
	def check_shortdesc_word_count(self, error_str, content, max_word_count=50):
		errors = []
		
		# Find all shortdesc elements with their line numbers using regex
		shortdesc_matches = self.find_elements_with_line_numbers(content, 'shortdesc')
		
		for line_num, shortdesc_text, match in shortdesc_matches:
			if shortdesc_text:
				shortdesc_word_count = len(shortdesc_text.split())
				if shortdesc_word_count > max_word_count:
					errors.append(ProgrammaticRyffineDITAError(
						line_num,
						error_str.format(
							shortdesc_word_count=shortdesc_word_count,
							max_word_count=max_word_count
						)
					))
		
		return errors

	def check_index_term_placement(self, error_str, content):
		pattern = r"(.{0,2})(<indexterm(?:[^>]*/>|[^>]*>.*?</indexterm>))(.{0,2})"
		errors = []
		
		matches = re.finditer(pattern, content, re.DOTALL)
		for match in matches:
			before, tag, after = match.groups()
			if not ((before.strip() and before.strip()[-1] in [">", "."]) or 
					(after.strip() and after.strip()[0] in ["<", "."])):
				# Calculate line number based on character position
				content_before_match = content[:match.start()]
				line_num = content_before_match.count('\n') + 1
				parent_element = self.find_parent_element(content, match.start())
				errors.append(ProgrammaticRyffineDITAError(
						line_num,
						error_str.format(
							parent_element=parent_element
						)
					))
				
		return errors

	def validate_content(self, content) -> List[ProgrammaticRyffineDITAError]:
		content = clean_dita(content)
		content = prettify_xml(content)
		all_errors = []
		for rule, func in self.programattic_checks.items():
			errors = func(rule, content)
			all_errors += errors

		return all_errors