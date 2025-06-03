# Ryffine DITA RNG Schemas

## Overview
These RNG schemas provide validation for Ryffine DITA content based on the Ryffine Information Model. The schemas are modular and independent of the DITA Open Toolkit.

## Directory Structure
```
/common/
  - ryffineCommonElements.rng    # Common block and inline elements
  - ryffineCommonAttributes.rng  # Common attributes
  - ryffineMetadata.rng          # Metadata elements (prolog, topicmeta)

/rng/
  - ryffineDita.rng              # Master schema - validates any DITA file
  - ryffineConcept.rng           # Concept topic schema
  - ryffineTask.rng              # Task topic schema
  - ryffineReference.rng         # Reference topic schema
  - ryffineTroubleshooting.rng   # Troubleshooting topic schema
  - ryffineGlossentry.rng        # Glossary entry schema
  - ryffineLearningOverview.rng  # Learning overview schema
  - ryffineMap.rng               # Map schema
  - ryffineBookmap.rng           # Bookmap schema
```

## Usage

### Validate Any DITA File
Use `rng/ryffineDita.rng` to validate any Ryffine DITA file (topic or map).

### Validate Specific File Types
Use the specific schema for the file type you're validating:
- Concepts: `rng/ryffineConcept.rng`
- Tasks: `rng/ryffineTask.rng`
- References: `rng/ryffineReference.rng`
- Troubleshooting: `rng/ryffineTroubleshooting.rng`
- Glossary entries: `rng/ryffineGlossentry.rng`
- Learning overviews: `rng/ryffineLearningOverview.rng`
- Maps: `rng/ryffineMap.rng`
- Bookmaps: `rng/ryffineBookmap.rng`

## Schema Features

### Common Elements
- Block elements: p, ul, ol, dl, note, fig, table, simpletable, codeblock, section, example
- Inline elements: uicontrol, filepath, menucascade, wintitle, codeph, varname, b, i, cite, term, ph, xref
- Table structures: CALS tables and simple tables
- Step elements: steps, substeps, choices, choicetable

### Metadata Support
- Topic metadata: prolog with author, source, critdates, permissions, audience, keywords, indexterms, prodinfo
- Map metadata: topicmeta with navtitle, shortdesc, audience, category, keywords

### Attributes
- Common: id, xml:lang
- Linking: href, format, scope, type, collection-type, linking
- Processing: toc, print, processing-role
- Display: frame, scale

## Extending the Schemas

To add new elements or attributes:
1. Add common elements to `/common/ryffineCommonElements.rng`
2. Add common attributes to `/common/ryffineCommonAttributes.rng`
3. Add topic-specific elements to the appropriate topic schema
4. The master schema (`ryffineDita.rng`) will automatically include all changes

## Notes
- These schemas follow the Ryffine Information Model specifications
- They are designed to be modular and maintainable
- All file names use camelCase convention
- The schemas support all information types defined in the Ryffine model

## Integration with XML Catalogs

While `ryffineDita.rng` is the master validation schema, you may want to create an XML catalog (`catalog.xml`) to:
- Map PUBLIC or SYSTEM identifiers to these schema files
- Enable XML processors to find schemas without absolute paths
- Support schema resolution in XML editors and processing tools

Example catalog entry:
```xml
<uri name="http://www.ryffine.com/dita/rng/ryffineDita.rng" 
     uri="rng/ryffineDita.rng"/>
```