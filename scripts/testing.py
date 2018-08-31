'''
Class created for testing new data against given model
'''
from sodapy import Socrata
import pandas as pd
import os
import json
from datetime import datetime, timedelta

class Testing():

    def __init__(self):
         # Domain , SODA API
        self.database_311 = "fhrw-4uyv"
        self.client = Socrata('data.cityofnewyork.us', 'tvPeTjPatFwjuelfpMNb0G8WH')
        #Save memory initiall by quirying only that what is need:
        self.select_sql = "agency,borough,closed_date,community_board,complaint_type,created_date,descriptor,open_data_channel_type,status,longitude,latitude"

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
        return self.data_frame
    def clean_data(self):
        '''
        Cleans data to be processed against pickle data setting unique id as index
        '''
        self.data_frame = self.data_frame[self.data_frame['status'] != 'Closed']
        self.data_frame['created_date'] = pd.to_datetime(self.data_frame['created_date'])

        #Ensure community boards are good
        self.data_frame = self.data_frame[self.data_frame['community_board'].isin(self.community_board_list)]
        #get date dummies
        self.data_frame['created_date_year'] = self.data_frame['created_date'].dt.year
        self.data_frame['created_date_month'] = self.data_frame['created_date'].dt.month
        self.data_frame['created_date_day'] = self.data_frame['created_date'].dt.day
        self.data_frame['created_date_hour'] = self.data_frame['created_date'].dt.hour
        self.data_frame['created_date_day_of_week'] = self.data_frame['created_date'].dt.dayofweek
        #Drop status & lat/long
        self.data_frame.drop(['status','latitude','longitude','created_date','closed_date'], axis=1 , inplace=True)

        #get rest of dummies
        self.data_frame = .get_dummies(self.data_frame, columns=['agency','borough','community_board',
                'complaint_type','descriptor','open_data_channel_type'])
        return self.data_frame
if __name__ == '__main__':
    print ('This program is being run by itself')
