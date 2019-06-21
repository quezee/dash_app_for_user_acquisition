from clickhouse_driver import Client
# import pandas as pd

class CHHandler:
    def __init__(self, host, port):
        self.conn = Client(host, port)

    def simple_query(self, query):
        response = self.conn.execute(query, with_column_types=False, settings={'max_execution_time': 3600})
        return response

    # def pandas_query(self, query):
    #     response = self.conn.execute(query, with_column_types=True, settings={'max_execution_time': 3600})
    #     data = response [0]
    #     cols = [row[0] for row in response [1]]
    #     return pd.DataFrame(data, columns=cols)


# if __name__ == '__main__':
#     table = 'appsflyer.installs'
#     dt_from = '2019-06-20 00:00:00'
#     dt_to = '2019-06-21 23:59:59'
#     app = 'Last Day on Earth'
#     plat = 'ios'
#
#     query = f'''
#     SELECT DISTINCT MediaSource FROM {table}
#     WHERE AttributedTouchTime BETWEEN '{dt_from}' AND '{dt_to}'
#     AND AppName = '{app}' AND Platform = '{plat}'
# '''
#     from config import Config
#     config = Config()
#     ch = CHHandler(config.DB_HOST, config.DB_PORT)
#
#     s = ch.simple_query(query)
#     # p = ch.pandas_query(query)