from tabula import read_pdf


class BankStatements(object):
    """Class for analysis of Bank Statements"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.tabula_params = {
            'pages': 'all',
            'guess': True,
            'pandas_options': {
                'error_bad_lines': False
            },
            'output_format': 'json'
        }
        self.pdf_json = self.__get_pdf_json()
        self.raw_data = self.__get_raw_data()

    def __get_pdf_json(self):
        return read_pdf(self.pdf_path, **self.tabula_params)

    def __get_raw_data(self):
        raw_data = {}
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
            raw_data = {
                "headers": rows_data_list[0],
                "body": rows_data_list[1:]
            }
        return raw_data
