import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .odttf import deobfuscate


class DocxFontExtractor(zipfile.ZipFile):
    def __init__(self, docx_file: str, output_dir: str, *args, **kwargs):
        super().__init__(docx_file, *args, **kwargs)

        self._output_dir = Path(output_dir)

        # Font IDs to paths
        self._map = {}

        # XML Namespaces
        self.rels_ns = {
            "": "http://schemas.openxmlformats.org/package/2006/relationships",
        }
        self.fonts_ns = {
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        }

    def _load_relationships(self):
        # Relationships for font IDs to their targets (or paths) are stored in
        # the fontTable.xml.rels file.
        rels = ET.fromstring(self.read("word/_rels/fontTable.xml.rels"))

        # Go through all entries and map the font IDs to their paths, so they
        # can be resolved later.
        for rel_entry in rels.findall(".//Relationship", self.rels_ns):
            font_id = rel_entry.attrib["Id"]
            font_path = rel_entry.attrib["Target"]

            self._map[font_id] = font_path

    def extract_fonts(self):
        self._load_relationships()

        # The actual entries for fonts that are used is stored in the fontTable.xml
        # file.
        fonts = ET.fromstring(self.read("word/fontTable.xml"))

        # Go through all <w:font> entries in the file
        for font in fonts.findall(".//w:font", self.fonts_ns):
            font_name = font.attrib["{" + self.fonts_ns["w"] + "}name"]

            # Check if the current font was embedded by searching for a
            # <w:embedRegular ...> child element.
            font_embed = font.find(".//w:embedRegular", self.fonts_ns)
            if font_embed is None:
                print(f"Skipping '{font_name}' because it's not embedded")
                continue

            # When "Embed only the characters used in the document" is checked,
            # word won't embed the complete font, but only a subset of it. In this
            # case it doesn't make sense to extract a partial font.
            font_subsetted = font_embed.attrib.get("{" + self.fonts_ns["w"] + "}subsetted")
            if font_subsetted is not None:
                print(f"Skipping '{font_name}' because only a subset of it is embedded")
                continue

            # Get the font ID and the related path from the previously created map
            font_id = font_embed.attrib["{" + self.fonts_ns["r"] + "}id"]
            font_path = self._map.get(font_id)
            if font_path is None:
                print(f"Skipping '{font_name}' because the font entry has no related path (?)")
                continue

            # Get the GUID and use it to deobfuscate the embedded font data
            font_guid = font_embed.attrib["{" + self.fonts_ns["w"] + "}fontKey"]
            font_data = deobfuscate(font_guid, self.read(f"word/{font_path}"))

            # Get the obfuscated file extension and strip the 'ob'
            obf_ext = font_path.rsplit(".", 1)[1]
            font_extension = obf_ext[2:]

            # Build a proper filename for the font
            font_filename = font_name + "." + font_extension
            font_filepath = self._output_dir / font_filename

            print(f"Extracting '{font_name}' to '{font_filepath}'")
            with font_filepath.open("wb") as fp:
                fp.write(font_data)
