import re
import datetime

MIN_COLUMNS = 5
MAX_COLUMNS = 5

HEADER = set(['Tran Date', 'Chq No', 'Particulars',
              'Debit', 'Credit', 'Balance', 'Init.'])

MAX_START_DAY_OF_MONTH = 5
MIN_END_DAY_OF_MONTH = 25


class AXISBankStatements(object):
    """Class to analyse the data obtained from AXIS Bank"""

    def __init__(self, raw_table_data, pdf_text):
        self.raw_table_data = raw_table_data
        self.pdf_text = pdf_text
        self.statements = []
        self.transactions = {}
        self.__set_statements_and_transaction()
        self.stats = {}
        self.__set_pdf_text_stats()
        self.all_day_transactions = self.__get_all_day_transactions()
        self.__set_stats()

    def __is_date(self, input_string):
        is_date = False
        try:
            datetime.datetime.strptime(input_string, '%d-%m-%Y')
            is_date = True
        except Exception as e:
            pass
        return is_date

    def __get_amount(self, input_string):
        comma_remove_input_string = input_string.replace(',', '')
        try:
            return float(comma_remove_input_string)
        except Exception as e:
            return 0.0

    def __deconcatinate_numbers(self, input_string):
        number_list = input_string.split(' ')
        if len(number_list) == 2:
            for index in xrange(0, len(number_list)):
                number_list[index] = self.__get_amount(number_list[index])
            return number_list
        return [0.0, 0.0]

    def __get_statement_set_transaction(self, data_list):
        statement_dict = {}
        try:
            if len(data_list) == MIN_COLUMNS and self.__is_date(data_list[0]):
                statement_dict = {
                    'transaction_date': datetime.datetime.strptime(data_list[0], '%d-%m-%Y'),
                    'cheque_no': data_list[-4],
                    'withdraw_deposit': self.__get_amount(data_list[-3]),
                    'balance': self.__get_amount(data_list[-2]),
                    'init_bank': data_list[-1],
                }
            if statement_dict:
                self.transactions[statement_dict[
                    'transaction_date']] = statement_dict['balance']
        except Exception as e:
            print "Following error occured while processing {data_list} : {error}".format(data_list=str(data_list), error=str(e))
        return statement_dict

    def __set_statements_and_transaction(self):
        for data_list in self.raw_table_data.get('body', []):
            if MIN_COLUMNS <= len(data_list) <= MAX_COLUMNS and not HEADER.intersection(set(data_list)):
                statement_dict = self.__get_statement_set_transaction(
                    data_list)
                self.statements.append(
                    statement_dict) if statement_dict else None

    def __get_pdf_dates(self):
        from_string_date_list = re.findall(
            r'(From : \d{2}-\d{2}-\d{4})', self.pdf_text)
        to_string_date_list = re.findall(
            r'(To : \d{2}-\d{2}-\d{4})', self.pdf_text)
        return [string_date.partition('From : ')[2] for string_date in from_string_date_list] + [string_date.partition('To : ')[2] for string_date in to_string_date_list]

    def __set_pdf_text_stats(self):
        self.stats['start_date'] = min(self.transactions.keys())
        self.stats['end_date'] = max(self.transactions.keys())
        all_string_date_list = self.__get_pdf_dates()
        all_date_list = []
        for string_date in all_string_date_list:
            try:
                all_date_list.append(
                    datetime.datetime.strptime(string_date, '%d-%m-%Y'))
            except Exception as e:
                pass
        self.stats['pdf_text_start_date'] = min(
            all_date_list) if all_date_list else self.stats['start_date']
        self.stats['pdf_text_end_date'] = max(
            all_date_list) if all_date_list else self.stats['end_date']
        self.stats['days'] = (self.stats['pdf_text_end_date'] -
                              self.stats['pdf_text_start_date'] + datetime.timedelta(1)).days

    def __get_first_day_balance(self):
        opening_balance = None
        for data_list in self.raw_table_data.get('body', []):
            if len(data_list) == 2 and data_list[0] == 'OPENING BALANCE':
                opening_balance = self.__get_amount(data_list[1])
        return opening_balance if opening_balance else self.transactions[self.stats['start_date']]

    def __get_all_day_transactions(self):
        all_day_transactions = {}
        all_day_transactions[self.stats[
            'pdf_text_start_date']] = self.__get_first_day_balance()
        for day_no in xrange(1, self.stats['days']):
            day_date = self.stats['start_date'] + \
                datetime.timedelta(days=day_no)
            all_day_transactions[day_date] = self.transactions[day_date] if self.transactions.get(
                day_date) else all_day_transactions[day_date - datetime.timedelta(days=1)]
        return all_day_transactions

    def __min_date(self):
        if self.stats['pdf_text_start_date'].day <= MAX_START_DAY_OF_MONTH:
            return self.stats['pdf_text_start_date']
        day = 1
        month = self.stats['pdf_text_start_date'].month + \
            1 if self.stats['pdf_text_start_date'].month != 12 else 1
        year = self.stats['pdf_text_start_date'].year if self.stats[
            'pdf_text_start_date'].month != 12 else self.stats['pdf_text_start_date'].year + 1
        return datetime.datetime(year, month, day)

    def __max_date(self):
        if self.stats['pdf_text_end_date'].day >= MIN_END_DAY_OF_MONTH:
            return self.stats['pdf_text_end_date']
        return datetime.datetime(self.stats['pdf_text_end_date'].year, self.stats['pdf_text_end_date'].month, 1) - datetime.timedelta(days=1)

    def get_days_above_given_balance_unpartial_months(self, given_balance):
        min_date = self.__min_date()
        max_date = self.__max_date()
        above_given_balance_daywise = {}
        for day, balance in self.all_day_transactions.iteritems():
            if balance >= given_balance and min_date <= day <= max_date:
                above_given_balance_daywise[day] = balance
        return {
            'given_balance': given_balance,
            'no_of_days': len(above_given_balance_daywise),
            'below_above_balance_daywise': above_given_balance_daywise,
        }

    def get_days_above_given_balance(self, given_balance):
        above_given_balance_daywise = {}
        for day, balance in self.all_day_transactions.iteritems():
            if balance >= given_balance:
                above_given_balance_daywise[day] = balance
        return {
            'given_balance': given_balance,
            'no_of_days': len(above_given_balance_daywise),
            'below_above_balance_daywise': above_given_balance_daywise,
        }

    def __set_stats(self):
        self.stats['average_balance'] = round(sum(
            self.all_day_transactions.values()) /
            len(self.all_day_transactions.values()), 2)
