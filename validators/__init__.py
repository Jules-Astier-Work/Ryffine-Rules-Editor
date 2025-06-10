import os
from pathlib import Path
from validators.utils import clean_dita, prettify_xml
from validators.programmatic_validator import ProgrammaticValidator
from validators.report_builder import ReportBuilder
from validators.rng_validator import RNGValidator

class RyffineDITAValidator:
    def __init__(self):
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.rng_validator = RNGValidator(ryffine_dita_path=current_dir / "..")
        self.programmatic_validator = ProgrammaticValidator()
        self.report_builder = ReportBuilder()

    def validate_content(self, content):
        content = clean_dita(content)
        content = prettify_xml(content)
        rng_result = self.rng_validator.validate_content(content)
        programmatic_result = self.programmatic_validator.validate_content(content)

        line_errors = rng_result.get_line_errors()
        for error in programmatic_result:
            if line_errors.get(error.line) is None:
                line_errors[error.line] = []
            line_errors[error.line].append(error.error)
        sorted_line_errors = dict(sorted(line_errors.items()))

        definitions = list(rng_result.get_general_definitions().values())

        return {
            "llm_report": self.report_builder.build_llm_report(
                 content=content,
                 line_errors=sorted_line_errors,
                 defintions=definitions
                ),
            "report_data": {
                "content": self.report_builder.add_line_number_context(content),
                "line_errors": sorted_line_errors,
                "definitions": definitions
            }
        }