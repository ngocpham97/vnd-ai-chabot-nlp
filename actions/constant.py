import os
from pathlib import Path

root_path = Path(os.path.dirname(os.path.abspath(__file__)))

def join_root_path(path):
    join_path = os.path.join(root_path, path)
    if not os.path.exists(join_path):
        os.makedirs(join_path)
    return join_path
# env path
ENVIRONMENT_CONFIG_FILE = os.path.join(root_path, '.env')

#table path
loan_information_table   = "loan_information_table"
loan_information_columns = ['loan_name', 'amount_of_money', 'methob', 'requirement', 'loan_term', 'interest_rate']
loan_register_table      = "loan_register"
loan_register_columns = ['id', 'username', 'id_card', 'telephone_number', 'amount_of_money']
