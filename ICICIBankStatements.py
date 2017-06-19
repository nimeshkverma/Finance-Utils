import datetime
from BankStatements import BankStatements

MIN_COLUMNS = 8
MAX_COLUMNS = 9

HEADER = set(['S No.', 'Value Date', 'Transaction Date', 'Cheque Number',
              'Transaction Remarks', 'Withdrawal Amount', 'Deposit Amount', 'Balance (INR )'])


class ICICIBankStatements(BankStatements):
    """Class to analyse the data obtained from ICICI Bank"""

    def __init__(self, pdf_path):
        super(ICICIBankStatements, self).__init__(pdf_path)
        self.statements = []
        self.transactions = {}
        self.__set_statements_and_transaction()
        self.stats = {}
        self.all_day_transactions = self.__get_all_day_transactions()
        self.__set_stats()

    def __get_statement_set_transaction(self, data_list):
        statement_dict = {}
        try:
            if len(data_list) in [8, 9]:
                statement_dict = {
                    'sr_no': data_list[0],
                    'value_date': datetime.datetime.strptime(data_list[1], '%d/%m/%Y'),
                    'transaction_date': datetime.datetime.strptime(data_list[2], '%d/%m/%Y'),
                    'cheque_no': data_list[3],
                }
                if len(data_list) == 8:
                    statement_dict.update({
                        'transaction_remark': str(data_list[4]),
                        'withdrawal_amount': float(data_list[5]),
                        'deposit_amount': float(data_list[6]),
                        'balance': float(data_list[7])
                    })
                elif len(data_list) == 9:
                    statement_dict.update({
                        'transaction_remark': str(data_list[4]) + str(data_list[5]),
                        'withdrawal_amount': float(data_list[6]),
                        'deposit_amount': float(data_list[7]),
                        'balance': float(data_list[8])
                    })
                else:
                    statement_dict = {}
                if statement_dict:
                    self.transactions[statement_dict[
                        'transaction_date']] = statement_dict['balance']
        except Exception as e:
            print "Following error occured while processing {data_list} : {error}".format(data_list=str(data_list), error=str(e))
        return statement_dict

    def __set_statements_and_transaction(self):
        for data_list in self.raw_data.get('body', []):
            if MIN_COLUMNS <= len(data_list) <= MAX_COLUMNS and not HEADER.intersection(set(data_list)):
                statement_dict = self.__get_statement_set_transaction(
                    data_list)
                self.statements.append(
                    statement_dict) if statement_dict else None

    def __get_all_day_transactions(self):
        all_day_transactions = {}
        self.stats['start_date'] = min(self.transactions.keys())
        self.stats['end_date'] = max(self.transactions.keys())
        self.stats['days'] = (
            self.stats['end_date'] - self.stats['start_date'] + datetime.timedelta(1)).days
        all_day_transactions[self.stats['start_date']
                             ] = self.transactions[self.stats['start_date']]
        for day_no in xrange(1, self.stats['days']):
            day_date = self.stats['start_date'] + \
                datetime.timedelta(days=day_no)
            all_day_transactions[day_date] = self.transactions[day_date] if self.transactions.get(
                day_date) else all_day_transactions[day_date - datetime.timedelta(days=1)]
        return all_day_transactions

    def __min_date(self):
        if self.stats['start_date'].day == 1:
            return self.stats['start_date']
        day = 1
        month = self.stats['start_date'].month + \
            1 if self.stats['start_date'].month != 12 else 1
        year = self.stats['start_date'].year if self.stats[
            'start_date'].month != 12 else self.stats['start_date'].year + 1
        return datetime.datetime(year, month, day)

    def __max_date(self):
        if self.stats['end_date'].day >= 25:
            return self.stats['end_date']
        return datetime.datetime(self.stats['end_date'].year, self.stats['end_date'].month, 1) - datetime.timedelta(days=1)

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
            self.all_day_transactions.values()) / len(self.all_day_transactions.values()), 2)
