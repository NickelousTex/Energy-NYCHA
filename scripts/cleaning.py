''' Take the most recent data from NYC 311 Open Data, and return all cases: '''
from sodapy import Socrata
import pandas as pd
import os
import json
class DataCleaner:
    def __init__(self):
        self.database_311 = "fhrw-4uyv"
        self.client = Socrata('data.cityofnewyork.us', 'tvPeTjPatFwjuelfpMNb0G8WH') # Domain , SODA API
        self.limit = 100000 # limited to 100k for time
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

    def get_data(self,date): #formated date should be year-month-day as string
        ''' pulls only the 100k most recent calls from inputed date from NYC 311'''
        formated_date = '{}T00:00:00.000'.format(date)
        query = "created_date > '{}' ".format(formated_date)
        results = self.client.get(self.database_311, select=self.select_sql, where=query, limit=self.limit)
        self.data_frame = pd.DataFrame.from_records(results)

    def clean_data(self):
        self.data_frame.dropna(subset=['closed_date','descriptor','latitude',
                                'longitude'], inplace=True)
        self.data_frame['latitude'] =(
        self.data_frame['latitude'].astype('float64')
        )
        self.data_frame['longitude'] =( self.data_frame['longitude'].astype('float64')
        )
        self.data_frame['created_date'] = pd.to_datetime(self.data_frame['created_date'])
        self.data_frame['closed_date'] = pd.to_datetime(self.data_frame['closed_date'])
        #Create time till resolution
        self.data_frame['time_till_resolution'] = self.data_frame['created_date'] - self.data_frame['closed_date']

        self.data_frame['time_till_resolution'] =(-round(
                                    self.data_frame['time_till_resolution'].astype(
                                    'timedelta64[s]')/3600,2))
        return self.data_frame

if __name__ == '__main__':
    print ('This program is being run by itself')
