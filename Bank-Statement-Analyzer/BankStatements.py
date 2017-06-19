import subprocess
import re
from cStringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from tabula import read_pdf

from ICICIBankStatements import ICICIBankStatements


class BankStatements(object):
    """Class for analysis of Bank Statements"""

    def __init__(self, pdf_path, password=''):
        self.pdf_path = pdf_path
        self.password = password
        self.tabula_params = {
            'pages': 'all',
            'guess': True,
            'pandas_options': {
                'error_bad_lines': False
            },
            'output_format': 'json'
        }
        self.pdf_json = self.__get_pdf_json()
        self.raw_table_data = self.__get_raw_table_data()
        self.pdf_text = self.__get_pdf_text()
        self.specific_bank = self.__get_specific_bank()

    def __get_pdf_json(self):
        return read_pdf(self.pdf_path, **self.tabula_params)

    def __get_decrypted_pdf_path(self):
        if '.pdf' in self.pdf_path:
            path_list = self.pdf_path.split('.pdf')
            return path_list[0] + '_decrypted.pdf'
        elif '.pdf' in self.pdf_path:
            path_list = self.pdf_path.split('.PDF')
            return path_list[0] + '_decrypted.pdf'
        else:
            self.pdf_path + +'_decrypted.pdf'

    def __get_pdf_text(self):
        pdf_text = ''
        pdf_path_decrypt = self.__get_decrypted_pdf_path()
        decrypt_command = 'qpdf --password={password} --decrypt {pdf_path} {pdf_path_decrypt}'.format(
            password=self.password, pdf_path=self.pdf_path, pdf_path_decrypt=pdf_path_decrypt)
        file_clean_command = 'rm {pdf_path_decrypt}'.format(
            pdf_path_decrypt=pdf_path_decrypt)
        subprocess.call(decrypt_command, shell=True)
        pdf_text = self.__pdf_to_text(pdf_path_decrypt)
        subprocess.call(file_clean_command, shell=True)
        return pdf_text

    def __get_raw_table_data(self):
        raw_table_data = {}
        rows_data_list = []
        for data_dict in self.pdf_json:
            for rows_data in data_dict.get('data', []):
                row_data_list = []
                for row_data in rows_data:
                    if row_data.get('text'):
                        row_data_list.append(row_data['text'])
                if row_data_list:
                    rows_data_list.append(row_data_list)
        if rows_data_list:
            raw_table_data = {
                'headers': rows_data_list[0],
                'body': rows_data_list[1:]
            }
        return raw_table_data

    def __pdf_to_text(self, pdf_path_decrypt):
        pagenums = set()
        output = StringIO()
        manager = PDFResourceManager()
        converter = TextConverter(manager, output, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)

        infile = file(pdf_path_decrypt, 'rb')
        for page in PDFPage.get_pages(infile, pagenums):
            interpreter.process_page(page)
        infile.close()
        converter.close()
        text = output.getvalue()
        output.close
        return text

    def __is_icici(self):
        for header in self.raw_table_data['headers']:
            if re.search('Transaction Remarks', header, re.IGNORECASE):
                return True
        return False

    def __get_specific_bank(self):
        if self.__is_icici():
            return ICICIBankStatements(self.raw_table_data, self.pdf_text)
        else:
            return None
