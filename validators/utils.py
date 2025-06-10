import re
from xml.dom import minidom


def prettify_xml(xml_string):
	dom = minidom.parseString(xml_string)
	pretty = dom.toprettyxml(indent="  ")
	pretty = pretty.replace('<?xml version="1.0" ?>\n', '')
	return re.sub(r'\n\s*\n', '\n', pretty).strip()

def clean_dita(dita_string):
    return re.sub(r'(<\?xml[\s\S]*?\?>|<!DOCTYPE[\s\S]*?>)', '', dita_string, flags=re.DOTALL)