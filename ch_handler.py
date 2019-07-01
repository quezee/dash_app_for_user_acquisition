from clickhouse_driver import Client
# import pandas as pd

class CHHandler:
    def __init__(self, host, port):
        self.conn = Client(host, port)

    def simple_query(self, query, column_types=False):
        response = self.conn.execute(query, with_column_types=column_types, settings={'max_execution_time': 3600})
        if column_types:
            data = [dict(zip([col[0] for col in response[1]], row)) for row in response[0]]
            cols = [{'name': col[0], 'id': col[0]} for col in response[1]]
            return data, cols
        data = [{'label': row[0], 'value': row[0]} for row in response]
        return data



    # def pandas_query(self, query):
    #     response = self.conn.execute(query, with_column_types=True, settings={'max_execution_time': 3600})
    #     data = response [0]
    #     cols = [row[0] for row in response [1]]
    #     return pd.DataFrame(data, columns=cols)


if __name__ == '__main__':

    start_date = '2019-06-01 00:00:00'
    end_date = '2019-07-01 23:59:59'
    app = "Forge of Glory"
    plat = 'ios'

    query = '''
    SELECT DISTINCT MediaSource FROM appsflyer.installs
    WHERE AttributedTouchTime BETWEEN {} AND {}
    AND AppName = {} AND Platform = {}
    '''.format(repr(start_date), repr(end_date), repr(app), repr(plat))

    from config import Config
    config = Config()
    ch = CHHandler(config.DB_HOST, config.DB_PORT)

    s = ch.simple_query(query, True)
    # p = ch.pandas_query(query)