from file_detector import detect_file_type

from engines.pdf_engine import PDFEngine

from parsers.csv_parser import read_csv
from parsers.excel_parser import read_excel
from parsers.json_parser import read_json
from parsers.xml_parser import read_xml
from parsers.ofx_parser import read_ofx
from parsers.txt_parser import read_txt


def read_statement(filepath):

    file_type = detect_file_type(filepath)

    if file_type == "pdf":

        engine = PDFEngine(filepath)

        return engine.build_dataframe()

    elif file_type == "csv":

        return read_csv(filepath)

    elif file_type == "excel":

        return read_excel(filepath)

    elif file_type == "json":

        return read_json(filepath)

    elif file_type == "xml":

        return read_xml(filepath)

    elif file_type == "ofx":

        return read_ofx(filepath)

    elif file_type == "txt":

        return read_txt(filepath)

    else:

        raise Exception("Unsupported File Type")