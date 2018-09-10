'''
Class created for testing new data against given model
'''
from sodapy import Socrata
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from sklearn.externals import joblib
import sqlite3
import schedule
import time

class PredictionsTable():

    def __init__(self):
         # Domain , SODA API
        self.database_311 = "fhrw-4uyv"
        self.client = Socrata('data.cityofnewyork.us', 'tvPeTjPatFwjuelfpMNb0G8WH')
        #Save memory initiall by quirying only that what is need:
        self.select_sql = "unique_key,agency,borough,closed_date,community_board,complaint_type,created_date,descriptor,open_data_channel_type,status,longitude,latitude"

        self.community_board_list = set(['06 BRONX', '01 BRONX', '14 QUEENS', '13 QUEENS',
        '13 BROOKLYN', '09 BROOKLYN', '10 QUEENS',
       '08 BRONX', '10 BRONX', '01 QUEENS', '11 QUEENS', '01 BROOKLYN',
       '12 BRONX', '14 BROOKLYN', '07 MANHATTAN', '04 MANHATTAN',
       '05 MANHATTAN', '07 BRONX', '06 QUEENS', '18 BROOKLYN',
       '02 STATEN ISLAND', '15 BROOKLYN', '07 QUEENS', '03 STATEN ISLAND',
       '03 QUEENS', '08 QUEENS', '01 STATEN ISLAND', '07 BROOKLYN',
       '04 BRONX', '12 BROOKLYN', '12 QUEENS',
       '17 BROOKLYN', '04 QUEENS', '03 BROOKLYN', '05 QUEENS',
       '02 QUEENS', '03 MANHATTAN', '11 BRONX', '10 BROOKLYN',
       '06 BROOKLYN', '11 BROOKLYN', '05 BROOKLYN', '04 BROOKLYN',
       '12 MANHATTAN', '09 QUEENS', '09 MANHATTAN', '10 MANHATTAN',
       '16 BROOKLYN', '09 BRONX', '05 BRONX', '02 BROOKLYN',
       '06 MANHATTAN', '02 BRONX', '08 BROOKLYN', '11 MANHATTAN',
       '08 MANHATTAN', '02 MANHATTAN',  '03 BRONX',
       '01 MANHATTAN'])
        pass


    def get_data(self, limit=1000):
        '''
        pulls the most recent 1k 311 calls from NYC open data
        '''
        time = datetime.utcnow()-timedelta(days=1)
        time_string = '{}-{}-{}T00:00:00.000'.format(time.year,time.month,time.day)
        query = "created_date > '{}' ".format(time_string)
        results = self.client.get(self.database_311, select=self.select_sql, where=query, limit=limit)
        self.data_frame = pd.DataFrame.from_records(results)


        pass

    def clean_data(self):
        '''
        Cleans data to be processed against pickle data setting unique id as index
        '''

        self.data_frame = self.data_frame[self.data_frame['status'] != 'Closed']
        self.data_frame['created_date'] = pd.to_datetime(self.data_frame['created_date'])

        #Ensure community boards are good
        self.data_frame = self.data_frame[self.data_frame['community_board'].isin(self.community_board_list)]

        #copy needed for later return
        self.data_frame.set_index('unique_key')
        self.predictions_data_frame = self.data_frame.copy()

        #get date dummies
        self.data_frame['created_date_year'] = self.data_frame['created_date'].dt.year
        self.data_frame['created_date_month'] = self.data_frame['created_date'].dt.month
        self.data_frame['created_date_day'] = self.data_frame['created_date'].dt.day
        self.data_frame['created_date_hour'] = self.data_frame['created_date'].dt.hour
        self.data_frame['created_date_day_of_week'] = self.data_frame['created_date'].dt.dayofweek
        #Drop status & lat/long
        self.data_frame.drop(['status','latitude','longitude','created_date','closed_date'], axis=1 , inplace=True)
        #get rest of dummies
        self.data_frame = pd.get_dummies(self.data_frame, columns=['agency','borough','community_board',
                'complaint_type','descriptor','open_data_channel_type'])
        #Find any unseen values and delete, replace with empty cols
        del_cols = joblib.load('../EDA/feature_names.pkl')
        self.data_frame = drop_cols(self.data_frame,del_cols)

        pass
    def predict(self):
        loaded_model = joblib.load('../EDA/gradient_boost_model.pkl')

        self.predictions_data_frame['Predicted_Time_To_Close'] = loaded_model.predict(self.data_frame)

        return self.predictions_data_frame.drop('closed_date',axis=1)

    def get_actual(self):
        print('Grabbing Unique_Keys...')
        engine = sqlite3.connect("../sql_tables/predictions_311.db3")
        unique_key = engine.execute("SELECT unique_key FROM predictions_311").fetchall()
        unique_key = tuple([x[0] for x in unique_key])
        engine.close()
        print('Done')

        time = datetime.utcnow()-timedelta(days=2)
        time_string = '{}-{}-{}T00:00:00.000'.format(time.year,time.month,time.day)
        query = "closed_date > '{}' ".format(time_string)
        print('Getting Closed Dates...')
        results = self.client.get(self.database_311, select=self.select_sql, where=query, limit=3000)
        data_frame = pd.DataFrame.from_records(results)
        print('Done.')
        keys = data_frame[data_frame['unique_key'].isin(unique_key)].unique_key.values
        actual = data_frame[data_frame['unique_key'].isin(unique_key)]
        print('Getting Actual Close Times...')

        actual.set_index('unique_key',inplace=True)
        actual.sort_index(inplace=True)

        created = actual['created_date'] = pd.to_datetime(actual['created_date'])
        closed = actual['closed_date'] = pd.to_datetime(actual['closed_date'])

        actual['Real_Time_To_Close'] = created - closed

        actual['Real_Time_To_Close']= (-round(
                                    actual['Real_Time_To_Close'].astype(
                                    'timedelta64[s]')/3600,2))


        print('Done')
        print('Finding Closed Dates from Predections SQL')
        sql_query = "SELECT * FROM predictions_311 WHERE unique_key IN {}".format(tuple(keys))
        connect=sqlite3.connect("../sql_tables/predictions_311.db3")
        predicted = pd.read_sql_query(sql=sql_query, con=connect)

        predicted.set_index('unique_key', inplace=True)
        predicted.sort_index(inplace=True)
        print('Done')
        predicted['Actual_Time'] = actual['Real_Time_To_Close']
        connect.close()
        return predicted

def drop_cols(df, del_cols):
    '''Drop columns not in data frame and reshape with dummy cols to achive correct shape '''

    for col in (set(df.columns) - del_cols):
        df.drop([col], axis=1,inplace=True)

    length_missing_cols = (df.shape[1] - 935) #hardcoded to model

    for i in range(-length_missing_cols):
        df['{}'.format(i)]= 0

    return df
def save_to_table(database, data_frame):
    engine = sqlite3.connect("../sql_tables/{}.db3".format(database))
    data_frame.to_sql('{}'.format(database), con=engine, if_exists='append')

    engine.close()
    pass
def sql_jobs():
    print('Getting predictions...')
    predictions = PredictionsTable()
    predictions.get_data()
    predictions.clean_data()
    predictions_dataframe = predictions.predict()
    print('Saving Predictions to SQL Table...')
    save_to_table('predictions_311', predictions_dataframe)

    print('Finding Actual Results ...')
    actual_times= PredictionsTable()
    results_dataframe = actual_times.get_actual()

    print('Saving Results to SQL Table')
    save_to_table('results_311', results_dataframe)
    pass
if __name__ == '__main__':
        schedule.every(.5).hours.do(sql_jobs) #Change this for EC2 instance


        while True:
            schedule.run_pending()
            time.sleep(1700)
