# import psycopg2
# import os
# import csv

# class PostgreSQL:
#     def __init__(self, host, port, username, password, database):
#         self.host     = host
#         self.port     = port
#         self.username = username
#         self.password = password
#         self.database = database
        
#         self.connection = psycopg2.connect(user=self.username,
#                                    password=self.password,
#                                    host=self.host,
#                                    port=self.port,
#                                    database=self.database)

#         self.cursor = self.connection.cursor()

#     def close(self):
#         if (self.connection):
#             self.cursor.close()
#             self.connection.close()
            

#     def select(self, table_name, columns, key_names=[], key_values=[], key_ops=[], order=False, reverse=False, like=False, limit=None, offset=None):
            
#         query = ' '.join(['SELECT', ('%s')%(', '.join(columns)), 'FROM', table_name])
#         num_keys = len(key_names)
#         assert num_keys == len(key_values)
#         if (like):
#             if(len(key_ops) == 0):
#                 key_ops = ['LIKE'] * num_keys

#             if(num_keys > 0):
#                 condition = ' WHERE ' + ' AND '.join(['%s %s '%(key_name, key_op) + '%s' for key_name, key_op in zip(key_names, key_ops)])
#                 query += condition
#             if(order):
#                 orderby = ' ORDER BY ' + str(order)
#                 query += orderby
#             if(reverse):
#                 query += ' DESC '
#             if(limit):
#                 query += ' LIMIT %d'%(limit)
#             if(offset):
#                 query += ' OFFSET %d'%(offset)

#         else:
#             if(len(key_ops) == 0):
#                 key_ops = ['='] * num_keys

#             if(num_keys > 0):
#                 condition = ' WHERE ' + ' AND '.join(['%s %s '%(key_name, key_op) + '%s' for key_name, key_op in zip(key_names, key_ops)])
#                 query += condition
#             if(order):
#                 orderby = ' ORDER BY ' + str(order)
#                 query += orderby
#             if(reverse):
#                 query += ' DESC '
#             if(limit):
#                 query += ' LIMIT %d'%(limit)
#             if(offset):
#                 query += ' OFFSET %d'%(offset)

#         # print(query, key_values)
#         self.cursor.execute(query, tuple(key_values))
#         data = self.cursor.fetchall()
#         return data

#     def update(self, table_name, target_columns, target_values, key_columns, key_values):
#         query = ' '.join(['UPDATE ', table_name, 'SET '])

#         num_updates = len(target_columns)
#         assert num_updates == len(target_values)

#         updates = ', '.join(['%s = '%(column) + '%s' for column in target_columns])
#         query += updates

#         num_keys = len(key_columns)
#         assert num_keys == len(key_values)

#         if(num_keys > 0):
#             condition = ' WHERE ' + ' AND '.join(['%s = '%(column) + '%s' for column in key_columns])
#             query += condition

#         # print(query)
#         self.cursor.execute(query, tuple(target_values + key_values))
#         self.connection.commit()

#     def insert(self, table_name, columns, values):
#         query = ' '.join(['INSERT INTO', table_name, ('(%s)')%(', '.join(columns)), 'VALUES', '(', ','.join(['%s']*len(values)) , ')'])
#         values = tuple(values)
#         # print('table', table_name)
#         # print(values)
#         self.cursor.execute(query, values)
#         self.connection.commit()

#     def delete(self, table_name, key_columns, key_values):
#         query = ' '.join(['DELETE FROM ', table_name])

#         condition = ' WHERE ' + ' AND '.join(['%s = '%(column) + '%s' for column in key_columns])
#         query += condition
#         self.cursor.execute(query, tuple(key_values))
#         self.connection.commit()

#     def list_loans(self):
#         list_loans = self.select(table_name='loan_information_table', columns=['loan_name', 'amount_of_money'])
#         return list_loans

#     def detail_loan(self, key_names, key_values):
#         detail = self.select(table_name='loan_information_table', columns=['loan_name', 'amount_of_money', 'methob', 'requirement', 'loan_term', 'interest_rate', 'disbursement_time'], key_names=key_names, key_values=key_values)
#         return detail


