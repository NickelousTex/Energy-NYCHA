'''
Create and quickly display Flagged calls for NYC 311 Data
Export and Save that data to AWS S3
'''
#Functions to run code
from geopy.distance import great_circle , vincenty
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
import pandas as pd
#Socrata is NYC's API
from sodapy import Socrata
import json
#Plotting Folium
import folium
from folium.plugins import MarkerCluster, HeatMap
#Save to S3
import boto3
#Schedule
import schedule
import time

class ComplaintsDisplay:
    '''
    Complaint = type of complaint to look for
    num_days = how many days back to query
    cluster_size = number of complaints within a distance in order to flag
    distance = IN METERS how close to determin if complaints should be clustered
    '''
    def __init__(self, complaint, num_days=1, cluster_size = 3, distance = 50):
     # Domain , SODA API
        self.database_311 = "fhrw-4uyv"
        self.client = Socrata('data.cityofnewyork.us', 'tvPeTjPatFwjuelfpMNb0G8WH')
    #Save memory initiall by quirying only that what is need:
        self.select_sql = "created_date,complaint_type,longitude,latitude"
        self.complaint = complaint
        self.num_days = num_days
        self.cluster_size = cluster_size
        self.distance = distance
    def complaints(self,):
        time = datetime.utcnow()-timedelta(days=self.num_days)
        time_string = '{}-{}-{}T00:00:00.000'.format(time.year,time.month,time.day)
        query = "created_date > '{}' AND complaint_type LIKE '%{}%' ".format(time_string, self.complaint)
        #Limit at 100k overrides default limit
        results = self.client.get(self.database_311, select=self.select_sql, where=query, limit=100000)
        self.data_frame = pd.DataFrame.from_records(results)

        coordinates = self.data_frame [['latitude', 'longitude']]
        coordinates = coordinates.convert_objects(convert_numeric=True)
        coordinates.dropna(inplace=True)

        total = DBSCAN(eps=self.distance, min_samples=3, metric=GreatCircleDistance, n_jobs=-1).fit(coordinates.values)

        complaints = pd.DataFrame(coordinates.values, columns=['Latitude', 'Longitude'])

        complaints['label'] = total.labels_

        NYC = [40.757937,-73.882155]
        means = complaints[complaints.label > -1].groupby('label').mean()
        MAX_Count = len(complaints[complaints.label > -1].groupby('label').mean())

        flag = folium.Map(location=NYC , zoom_start=11)
        for each in means[0:MAX_Count].iterrows():
            folium.Marker(location = [each[1]['Latitude'],each[1]['Longitude']]).add_to(flag)

        hm = HeatMap([[0,0]])
        hm.add_to(flag)
        flag.save('../{}_complaints_flagged.html'.format(self.complaint))

        pass

def GreatCircleDistance(x, y):
    '''
    Finding distance on a sphere
    '''
    lat1, lon1 = x[0], x[1]
    lat2, lon2 = y[0], y[1]
    return great_circle((lat1, lon1), (lat2, lon2)).meters
def SaveToS3(file_str):
    client = boto3.client('s3') #low-level functional API
    resource = boto3.resource('s3') #high-level object-oriented API
    my_bucket = resource.Bucket('capstone311-bucket')

    my_bucket.upload_file('../{}'.format(file_str), Key='{}'.format(file_str), ExtraArgs={'ACL':'public-read'})
def MappingJobs():
    print('Generating Map 1 of 4...')
    display_noise_complaints = ComplaintsDisplay('Noise')
    display_noise_complaints.complaints()
    print('Saving Map...')
    SaveToS3('Noise_complaints_flagged.html')

    print('Generating Map 2 of 4...')
    display_rodent_complaints = ComplaintsDisplay('Rodent', num_days=7)
    display_rodent_complaints.complaints()
    SaveToS3('Rodent_complaints_flagged.html')
    print('Saving Map...')

    print('Generating Map 3 of 4...')
    display_Bulky_complaints = ComplaintsDisplay('Bulky', num_days=7)
    display_Bulky_complaints.complaints()
    SaveToS3('Bulky_complaints_flagged.html')
    print('Saving Map...')

    print('Generating Map 4 of 4...')
    display_Homeless_complaints = ComplaintsDisplay('Homeless', num_days=7,cluster_size = 5, distance = 100)
    display_Homeless_complaints.complaints()
    SaveToS3('Homeless_complaints_flagged.html')
    print('Saving Map...')
    print('Maps Complete')

if __name__ == '__main__':
    # schedule.every(12).hours.do(MappingJobs)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(14400)
    MappingJobs()
