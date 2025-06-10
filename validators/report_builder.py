from typing import Dict, List


class ReportBuilder:
	LLM_FEEDBACK_PROMPT = """
You are an Expert at writing RyffineDITA, a specialized version of DITA.
Here is a report of a previous failed attpemt to write RyffineDITA.
There is a comprehensive list of rules that were violated.
Rewrite the RyffineDITA content and fix the errors raised.
IMPORTANT: Output ONLY the new RyffineDITA content.
"""

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
	
	def get_line_report(self, line_number, errors: List[str]):
		return f"""
- Line {line_number}:
	{"\n	".join([error for error in errors])}"""

	def build_llm_report(self, content: str, line_errors: Dict[int, List[str]], defintions: List[str]=None):

		report =  f"""
{self.LLM_FEEDBACK_PROMPT}
Generated DITA Content:
{self.add_line_number_context(content)}
-----------------------------------------------
Errors:
{"\n".join([self.get_line_report(k, v) for k, v in line_errors.items()])}
"""
		
		if defintions is not None:
			report += f"""-----------------------------------------------
Definitions:

{"\n\n".join(defintions)}
"""
		return report