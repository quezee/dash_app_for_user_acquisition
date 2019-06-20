from clickhouse_driver import Client
import pandas as pd

class CHHandler:
    def __init__(self, host, port):
        self.conn = Client(host, port)

    def simple_query(self, query):
        response = conn.execute(query, with_column_types=False, settings={'max_execution_time': 3600})
        return response

    def pandas_query(self, query):
        response = conn.execute(query, with_column_types=True, settings={'max_execution_time': 3600})
        data = response [0]
        cols = [row[0] for row in response [1]]
        return pd.DataFrame(data, columns=cols)
