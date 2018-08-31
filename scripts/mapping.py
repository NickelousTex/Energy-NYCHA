''' Mapping with various clients in one Class'''
import folium
from folium import plugins
from folium.plugins import HeatMap
import plotly.plotly as py
import plotly.graph_objs as go
from IPython.display import HTML

class Map311():
    def __init__(self):
        pass

    def heat_map(self, dataframe,inquiry: str ):
        map_311 = folium.Map(location=[40.757937,-73.882155], zoom_start=11,
                     tiles= "Stamen Terrain")
        data = dataframe[dataframe['complaint_type']==inquiry][['latitude','longitude']].values

        hm = plugins.HeatMap(data,radius=15)
        hm.add_to(map_311)
        return map_311

    def bar_plot(self,series,name_str,num_to_show =10, input_text=None): #Input text for getting specific
        total = go.Bar(x=series.index[:num_to_show],
                      y=series.values[:num_to_show],
                      text=input_text)
        data = [total]
        return py.iplot(data, filename=name_str)

    def pie_chart(self, data_frame,search_str):
        search_values = data_frame[search_str].value_counts()[:10]
        labels , values = search_values.index , search_values.values
        trace = go.Pie(labels=labels, values=values)

        return py.iplot([trace], filename='basic_pie_chart')

if __name__ == '__main__':
    print ('This program is being run by itself')
