import argparse
import os

from docxfontext.extractor import DocxFontExtractor


def main():
    parser = argparse.ArgumentParser(description="Extract embedded fonts from .docx files")
    parser.add_argument("file", nargs="+", help="One or more .docx files to process")
    parser.add_argument("-o", "--output-dir", default=os.getcwd(), help="Optional output directory for extracted fonts")

    args = parser.parse_args()

    for file in args.file:
        extractor = DocxFontExtractor(file, output_dir=args.output_dir)
        extractor.extract_fonts()


if __name__ == "__main__":
    main()
