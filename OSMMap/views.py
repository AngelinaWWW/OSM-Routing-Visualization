from django.shortcuts import render
from django.shortcuts import render
from django.shortcuts import HttpResponse
import certifi
import ssl
import os
import geopy.geocoders
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
import requests
import xmltodict
import json
import numpy as np
import re


filepath_graph = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + '/leaflet/graph.graphml'
city = ox.load_graphml(filepath_graph)

filepath_cinema = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + '/leaflet/Cinema_HongKong.geojson'
with open(filepath_cinema, 'r') as load_f:
    cinemas_dict = json.load(load_f)

filepath_restaurant = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + '/leaflet/RestaurantOSM.geojson'
with open(filepath_restaurant, 'r') as load_f:
    restaurants_dict = json.load(load_f)
    #print(load_dict)

# Create your views here.
def index(request):
    return render(request, 'index.html')

def SPquery(request):
    #return HttpResponse("hello, 小蟒社区")
    start = request.GET.get('start')
    destination = request.GET.get('end')

    #if start is None and destination is None:
        #return render(request, 'index.html')

    origin_point = getLocationByGeo(start)
    destination_point = getLocationByGeo(destination)

    #print(city2)
    origin_node = ox.get_nearest_node(city, origin_point)
    destination_node = ox.get_nearest_node(city, destination_point)  # 获取D最邻近的道路节点
    #print(destination_node)
    route = nx.shortest_path(city, origin_node, destination_node, weight='length')# 请求获取最短路径
    routeleaflet = idtolatlon(route)
    #print(route)
    distance = nx.shortest_path_length(city, origin_node, destination_node, weight='length')

    return render(request, 'index.html',{'start':origin_point, 'destination':destination_point, 'route':json.dumps(routeleaflet), 'distance':distance})
'''
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        return render(request, 'index.html', {'wx_name': username+'，欢迎关注小蟒社区'})
    return render(request, 'login.html')'''
def KNNquery(request):
    POI = request.POST.get('POIs')
    if POI == 'cinemas':
        pois_dict = cinemas_dict
    elif POI == 'restaurant':
        pois_dict = restaurants_dict
    else:
        pass
    #knnlocation = request.POST.get('KNNlocation')
    knnlocation = request.POST.get('hiddenflag')
    k = int(request.POST.get('kvalue'))
    print(k)
    if knnlocation == 'Current location':
        knnlocation = request.POST.get('KNNlocation')
        knn_point = getLocationByGeo(knnlocation)
        pois_matrix = get_pois_matrix(pois_dict)
        knnlocation_matrix = np.zeros((1,2))
        knnlocation_matrix[0] = knn_point
        print(knnlocation_matrix)
        pois_indices, pois_distances = knn_distances(pois_matrix, knnlocation_matrix, k)
    else:
        knnlocation = request.POST.get('hiddenflag')
        knn_point = re.findall(r"\d+\.?\d*", str(knnlocation))
        print(knn_point)
        pois_matrix = get_pois_matrix(pois_dict)
        knnlocation_matrix = np.zeros((1, 2))
        knnlocation_matrix[0][0] = float(knn_point[0])
        knnlocation_matrix[0][1] = float(knn_point[1])
        print(knnlocation_matrix)
        pois_indices, pois_distances = knn_distances(pois_matrix, knnlocation_matrix, k)
    pois_name, pois_latlon = get_pois_info(pois_indices, pois_matrix, pois_dict)
    print(pois_name, pois_latlon)
    print(json.dumps(pois_name))
    print(json.dumps(pois_latlon))
    #return render(request, 'index.html', {'knnlocation': knnlocation, 'pois_indices':pois_indices, 'pois_distances':pois_distances,'pois_name':json.dumps(pois_name), 'pois_latlon':json.dumps(pois_latlon)})
    return render(request, 'index.html',
                  {'pois_name': json.dumps(pois_name), 'pois_latlon': json.dumps(pois_latlon)})
def getLocationByGeo(cityname):
    #知道地址获取经纬度

    ctx = ssl._create_unverified_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ctx


    geolocator = Nominatim(user_agent="OSMApp")

    location2 = geolocator.geocode(cityname)
    lat = location2.latitude
    lng = location2.longitude
    return (lat,lng)
'''
def idtolatlon(route):
    routeleaflet = []
    for i in range(len(route)):
        location = route[i]
        response = requests.get("https://www.openstreetmap.org/api/0.6/node/"+str(route[i])).text
        data = xmltodict.parse(response)
        lat = float(data['osm']['node']['@lat'])
        lon = float(data['osm']['node']['@lon'])
        locationleaflet = [lat, lon]
        routeleaflet.append(locationleaflet)
    print(routeleaflet)
    return routeleaflet'''

def idtolatlon(route):
    routeleaflet = []
    for i in route:
        location = city.nodes[i]
        latitude = location['y']
        longtitude = location['x']
        locationleaflet = [latitude, longtitude]
        routeleaflet.append(locationleaflet)
    print(routeleaflet)
    return routeleaflet

def knn_distances(poi_position, current_position, k):
    """
    Finds the k nearest neighbors of xTest in xTrain.
    Input:
    xTrain = n x d matrix. n=rows and d=features
    xTest = m x d matrix. m=rows and d=features (same amount of features as xTrain)
    k = number of nearest neighbors to be found
    Output:
    dists = distances between all xTrain and all XTest points. Size of n x m
    indices = k x m matrix with the indices of the yTrain labels that represent the point
    """
    # the following formula calculates the Euclidean distances.
    distances = np.zeros((len(poi_position), len(current_position)))
    #print(distances)
    for i in range(len(poi_position)):
        distance = ox.distance.great_circle_vec(poi_position[i][0], poi_position[i][1], current_position[0][0],
                                                current_position[0][1], earth_radius=6371009)
        distances[i] = distance
    # distances = -2 * xTrain @ xTest.T + np.sum(xTest ** 2, axis=1) + np.sum(xTrain ** 2, axis=1)[:, np.newaxis]
    # because of float precision, some small numbers can become negatives. Need to be replace with 0.
    distances[distances < 0] = 0
    #distances = distances ** .5
    indices = np.argsort(distances, 0)  # get indices of sorted items
    distances = np.sort(distances, 0)  # distances sorted in axis 0
    # returning the top-k closest distances.
    #print(indices[0:k, :], distances[0:k, :])
    return indices[0:k, :], distances[0:k, :]


def get_pois_matrix(pois_dict):
    pois_matrix = np.zeros((len(pois_dict['features']), 2))
    i = 0
    for poi_dict in pois_dict['features']:
        pois_matrix[i][0] = poi_dict["geometry"]["coordinates"][1]
        pois_matrix[i][1] = poi_dict["geometry"]["coordinates"][0]
        i += 1
    #print(pois_matrix)
    return pois_matrix

def get_pois_info(pois_indices, pois_matrix, pois_dict):
    pois_name = []
    pois_latlon = []
    for j in range(len(pois_indices)):
        try:
            poi_name = pois_dict['features'][pois_indices[j][0]]['properties']['name']
        except:
            poi_name = 'None'
        else:
            poi_name = pois_dict['features'][pois_indices[j][0]]['properties']['name']
        pois_name.append(poi_name.replace("'", ''))
        pois_latlon.append((pois_matrix[pois_indices[j][0]]).tolist())
    print(len(pois_name))
    print(pois_name, pois_latlon)
    return pois_name, pois_latlon
