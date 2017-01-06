import uuid
from flask import Flask
import requests
from pymongo import MongoClient
from bson import ObjectId
import json
from flask import jsonify
from flask import request
from flask import Response
from flask import json
from flask import render_template
from requests.auth import HTTPBasicAuth
from collections import OrderedDict
app=Flask(__name__)

location_counter=0
co_ordinates_dict=OrderedDict()
cost_check_dict=OrderedDict()
lyft_string=""
uber_string=""

String = ""
ubermatrix=[]
ubermatrix1=[]
ubermatrix2=[]

lyftmatrix=[]
lyftmatrix1=[]
lyftmatrix2=[]
lyft_roundtrip={}
uber_roundtrip={}
lyft_roundtrip_time={}
lyft_roundtrip_miles={}
uber_roundtrip_time={}
uber_roundtrip_miles={}

check_roundtrip=True

client = MongoClient('mongodb://test:test@ds127968.mlab.com:27968/cmpe273ritvick')
db = client['cmpe273ritvick']

collection = db['testtable']
locationsCollection = db['locations']
tripsCollection = db['trips']

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj

@app.route('/lyft')
def lyftapi():
    #response=requests.get("https://api.lyft.com/v1/lyft_cost?start_lat=37.7772&start_lng=-122.4233&end_lat=37.7972&end_lng=-122.4533")
    lyft_token_url = "https://api.lyft.com/oauth/lyft_token"
    lyft_token_headers = {'Content-Type':"application/json",'cache-control': "no-cache"}
    lyft_token=requests.post(lyft_token_url,headers=lyft_token_headers,auth=HTTPBasicAuth('hHrCBjFEyQ_Z', '0R-90jRMThfUKHGQRhaO-RW2AVExOzrk'),json={'grant_type': "client_credentials", 'scope': "public"})
    lyft_token_data=lyft_token.json()
    access_lyft_token=lyft_token_data['access_lyft_token']
    access_lyft_token = "gAAAAABYSNAkMcplZ48nVeG7Lh3pjszKK4vOVHH7X2ewCimfZbisShWghbaWUwVTSqr2LlC_JQUoXDdhYOOcWtr94fQwUP0TdoqjLL0hZmtI0AtdLR6j-yx6oSs0exT1e8tRqlan3bFTcLzeiht6zbv70xkZar8svDkUTjsVTpufaNm9f7dmk8fBnYWMDtY6KC9kFwdyIQFgH3c7ea6xj1ZoxW5JVW07XQ=="
    lyft_cost_url="https://api.lyft.com/v1/lyft_cost?ride_type=lyft&start_lat=37.329825&start_lng=-121.904980&end_lat=37.335409&end_lng=-121.881093"
    lyft_cost_headers={'Authorization': "Bearer"+" "+access_lyft_token}
    lyft_cost=requests.get(lyft_cost_url,headers=lyft_cost_headers)
    lyft_cost_data=lyft_cost.json()
    return jsonify(lyft_cost_data)

@app.route('/', methods=['GET'])
def loadIndex():
    return render_template("index.html")
    
@app.route('/locations', methods=['POST'])
def store_locations():
    global locationsCollection
    requestData = request.get_json(force=True)

        
    name= requestData["name"]
    address = requestData["address"]
    city = requestData["city"]
    state = requestData["state"]
    zipcode = requestData["zip"]
    
    obj1 = UbervsLyft()

    addressString=address + " " + city + " " + state + " " + zipcode

    parameters = obj1.url_parameters(addressString)

    coordinates = obj1.get_coordinates(parameters)

    if coordinates == None:

        return Response(response = json.dumps({"status" : "Invalid Address"}, cls=Encoder))
    else:
        # Mongo Insert here

        latlong = coordinates.split(",")



        coordinate = {}
        coordinate["lat"] = latlong[0]
        coordinate["lng"] = latlong[1]

        responseData = {}
        responseData["id"] =  str(uuid.uuid1())
        responseData["address"] = address
        responseData["city"] = city
        responseData["state"] = state
        responseData["zip"] = zipcode
        responseData["coordinate"] = coordinate
        responseData["name"] = name

        insertData = responseData
        inserted_id = locationsCollection.insert_one(insertData).inserted_id

        return Response(response = json.dumps(responseData, cls=Encoder))
    

    

@app.route('/locations/<locationId>', methods=['GET'])
def fetchLocation(locationId):
    global locationsCollection
    doc = locationsCollection.find_one({
        "id" : locationId
        })
    return Response(response = json.dumps(doc, cls=Encoder))

@app.route('/locations/<locationId>', methods=['PUT'])
def updateLocation(locationId):
    global locationsCollection
    doc = locationsCollection.find_one({
        "id" : locationId
        })

    requestData = request.get_json(force=True)

    doc["name"] = requestData["name"]

    locationsCollection.update({'_id':doc["_id"]}, {"$set": doc}, upsert=False)

    return Response(response = json.dumps(doc, cls=Encoder))

@app.route('/locations/<locationId>', methods=['DELETE'])
def deleteLocation(locationId):
    global locationsCollection
    doc = locationsCollection.find_one({
        "id" : locationId
        })
    locationsCollection.delete_many({"id": locationId})
    return Response(response = json.dumps(doc, cls=Encoder))


@app.route('/trips', methods=['POST'])
def calculateTrip():
    global location_counter
    global co_ordinates_dict

    requestData = request.get_json(force=True)

    startId = requestData["start"].replace("/locations/","")
    location_counter = 0
    print(startId)
    startDoc = locationsCollection.find_one({
        "id" : startId
        })

    

    #print(startDoc["name"])
    co_ordinates_dict[startDoc["id"]] = startDoc["coordinate"]["lat"] + "," + startDoc["coordinate"]["lng"]
    location_counter = location_counter + 1

    for i in range (0, len(requestData["others"])):
        
        otherId = requestData["others"][i].replace("/locations/","")
        otherDoc = locationsCollection.find_one({
        "id" : otherId
        })
        co_ordinates_dict[otherDoc["id"]] = otherDoc["coordinate"]["lat"] + "," + otherDoc["coordinate"]["lng"]
        location_counter = location_counter + 1

    for i in range(0,location_counter+1):
        lyftmatrix.append([])
        ubermatrix.append([])
        ubermatrix1.append([])
        ubermatrix2.append([])
        lyftmatrix1.append([])
        lyftmatrix2.append([])
    
    ubermatrix[0].append('')
    ubermatrix1[0].append('')
    ubermatrix2[0].append('')
    lyftmatrix[0].append('')
    lyftmatrix1[0].append('')
    lyftmatrix2[0].append('')
    
    #print co_ordinates_dict
    #print "location counter="
    #print location_counter
    for i in range(0,location_counter):
        print "i"
        print i
        ubermatrix[0].append(co_ordinates_dict.keys()[i])
        ubermatrix1[0].append(co_ordinates_dict.keys()[i])
        ubermatrix2[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix1[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix2[0].append(co_ordinates_dict.keys()[i])
    
    for i in range(0,location_counter):    
        ubermatrix[i+1].append(co_ordinates_dict.keys()[i])
        ubermatrix1[i+1].append(co_ordinates_dict.keys()[i])
        ubermatrix2[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix1[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix2[i+1].append(co_ordinates_dict.keys()[i])
    
    obj = UbervsLyft()

    lyft_string=obj.lyft_cost()
    
    uber_string=obj.uber_cost()
    
    result_string=""
    newobjnew=obj.Djikstra()
    
    del lyftmatrix[:]
    del ubermatrix[:]
    co_ordinates_dict.clear()

    responseData = {}
    responseData["id"] = str(uuid.uuid1())
    responseData["start"] = requestData["start"]
    responseData["end"] = requestData["start"]
    
    best_route_by_costs = []
    path = newobjnew[0]["path"];


    locs = path.split(",")
    
    j=0;
    for i in range(1, len(locs) - 1):
        best_route_by_costs.append('/locations/' + locs[i])
        j = j+1

    responseData["best_route_by_costs"] =  best_route_by_costs 
    newobjnew[0].pop("path")
    newobjnew[1].pop("path")
    responseData["providers"] = newobjnew


    inserted_id = tripsCollection.insert_one(responseData).inserted_id

    return Response(response = json.dumps(responseData, cls=Encoder))

   
        
@app.route('/form', methods=['POST'])
def form_matrix():
    global lyft_string
    global uber_string
    global location_counter
    global co_ordinates_dict
    global ubermatrix
    global lyftmatrix
    global lyftmatrix1
    global lyftmatrix2
    global check_roundtrip
    global String
    check_roundtrip=True
    location_counter=0
    
    
    obj=UbervsLyft()
    starting_location=request.form['starting_location']
    first_location=request.form['first']
    second_location=request.form['second']
    third_location=request.form['third']
    fourth_location=request.form['fourth']
    fifth_location=request.form['fifth']
    
    if starting_location:
        location_counter=location_counter+1
        starting_location_parameters=obj.url_parameters(starting_location)
        starting_location_coordinates=obj.get_coordinates(starting_location_parameters)
        if starting_location_coordinates==None:
            #print "starting location"
            return "Invalid Address"
        co_ordinates_dict[starting_location]=starting_location_coordinates
    
    if first_location:
        location_counter=location_counter+1
        first_location_parameters=obj.url_parameters(first_location)
        first_location_coordinates=obj.get_coordinates(first_location_parameters)
        if first_location_coordinates==None:
            #print "1st location"
            return "Invalid Address"
        co_ordinates_dict[first_location]=first_location_coordinates
        
    if second_location:
        location_counter=location_counter+1
        second_location_parameters=obj.url_parameters(second_location)
        second_location_coordinates=obj.get_coordinates(second_location_parameters)
        if second_location_coordinates==None:
            #print "2nd location"
            return "Invalid Address"
        co_ordinates_dict[second_location]=second_location_coordinates
    
    if third_location:
        location_counter=location_counter+1
        third_location_parameters=obj.url_parameters(third_location)
        third_location_coordinates=obj.get_coordinates(third_location_parameters)
        if third_location_coordinates==None:
            #print "3rd location"
            return "Invalid Address"
        co_ordinates_dict[third_location]=third_location_coordinates
    
    if fourth_location:
        location_counter=location_counter+1
        fourth_location_parameters=obj.url_parameters(fourth_location)
        fourth_location_coordinates=obj.get_coordinates(fourth_location_parameters)
        if fourth_location_coordinates==None:
            #print "4th location"
            return "Invalid Address"
        co_ordinates_dict[fourth_location]=fourth_location_coordinates
        
    if fifth_location:
        location_counter=location_counter+1
        fifth_location_parameters=obj.url_parameters(fifth_location)
        fifth_location_coordinates=obj.get_coordinates(fifth_location_parameters)
        if fifth_location_coordinates==None:
            #print "5th location"
            return "Invalid Address"
        co_ordinates_dict[fifth_location]=fifth_location_coordinates
    
    """"
    co_ordinates_dict[starting_location]=starting_location_coordinates
    if first_location:
        co_ordinates_dict[first_location]=first_location_coordinates
    if second_location:
        co_ordinates_dict[second_location]=second_location_coordinates
    if third_location:
        co_ordinates_dict[third_location]=third_location_coordinates
    if fourth_location:
        co_ordinates_dict[fourth_location]=fourth_location_coordinates
    if fifth_location:
        co_ordinates_dict[fifth_location]=fifth_location_coordinates
    """
    
    for i in range(0,location_counter+1):
        lyftmatrix.append([])
        ubermatrix.append([])
        ubermatrix1.append([])
        ubermatrix2.append([])
        lyftmatrix1.append([])
        lyftmatrix2.append([])
    
    ubermatrix[0].append('')
    ubermatrix1[0].append('')
    ubermatrix2[0].append('')
    lyftmatrix[0].append('')
    lyftmatrix1[0].append('')
    lyftmatrix2[0].append('')
    
    #print co_ordinates_dict
    #print "location counter="
    #print location_counter
    for i in range(0,location_counter):
        #print "i"
        #print i
        ubermatrix[0].append(co_ordinates_dict.keys()[i])
        ubermatrix1[0].append(co_ordinates_dict.keys()[i])
        ubermatrix2[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix1[0].append(co_ordinates_dict.keys()[i])
        lyftmatrix2[0].append(co_ordinates_dict.keys()[i])
    
    for i in range(0,location_counter):    
        ubermatrix[i+1].append(co_ordinates_dict.keys()[i])
        ubermatrix1[i+1].append(co_ordinates_dict.keys()[i])
        ubermatrix2[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix1[i+1].append(co_ordinates_dict.keys()[i])
        lyftmatrix2[i+1].append(co_ordinates_dict.keys()[i])
        
    lyft_string=obj.lyft_cost()
    ##print "lyft_string"
    ##print lyft_string
    ##print "lyftmatrix="
    ##print lyftmatrix
    ##print "cost_check="
    ##print cost_check_dict
    print lyftmatrix2
    #print lyftmatrix1
    #print lyftmatrix
    uber_string=obj.uber_cost()
    """#print lyftmatrix"""
    #print "uber string"
    #print uber_string
    result_string=""
    result_string=obj.Djikstra()
    
    del lyftmatrix[:]
    del lyftmatrix1[:]
    del lyftmatrix2[:]
    del ubermatrix[:]
    del ubermatrix1[:]
    del ubermatrix2[:]
    co_ordinates_dict.clear()
    
    
    r = json.dumps(result_string, cls=Encoder)
    print(r)
    return render_template('index.html', res=r);
    
    
class UbervsLyft:
    def __init__(self):
        pass
    
    def url_parameters(self,location):
        address=location.split()
        parameters=""
        for i in address:
            if not parameters:
                parameters=parameters+i
            else:
                parameters=parameters+"+"+i
        return parameters
        
    def get_coordinates(self, parameters):
        url="https://maps.googleapis.com/maps/api/geocode/json?address="+parameters
        geo_json=requests.get(url)
        geo_json=geo_json.json()
        if geo_json['status']=="ZERO_RESULTS":
            return None
        geo_coord=geo_json['results']
        geo_co=geo_coord[0]['geometry']
        co=geo_co['location']
        coordinates=str(co['lat'])+","+str(co['lng'])
        return coordinates
            
    def lyft_cost(self):
        global cost_check_dict
        global location_counter
        global lyftmatrix
        global lyftmatrix1
        global co_ordinates_dict
        global String
        lyft_token_url = "https://api.lyft.com/oauth/token"
        lyft_token_headers = {'Content-Type':"application/json",'cache-control': "no-cache"}
        lyft_token=requests.post(lyft_token_url,headers=lyft_token_headers,auth=HTTPBasicAuth('hHrCBjFEyQ_Z', '0R-90jRMThfUKHGQRhaO-RW2AVExOzrk'),json={'grant_type': "client_credentials", 'scope': "public"})
        lyft_token_data=lyft_token.json()
        access_lyft_token=lyft_token_data['access_token']
        #access_lyft_token = "gAAAAABYSNM_d6RVl-psx6yMfdNfa709TAKM4RhBqMiDPv6-ZFFG-pbAXXl5BigEIJxOMKajc2UlTsygnKmZbuvaZ2oZ8pdXIYTguHHWgwekvZ2T0Ti7QSnYZcGUbvpdsxDPL2NUus_eW5_GPMz6zL_r5RgZDqWK7LV8_xaoYp3CBaXNBXGgVnxQo-yfMMjt3kAHbIQyPqxInNPKx26iVQ3Mex-CUt5gbg=="
        
        for i in range(0,location_counter):
            for j in range(0,location_counter):
                if i==j:
                    lyftmatrix[i+1].append(1000)
                    lyftmatrix1[i+1].append(1000)
                    lyftmatrix2[i+1].append(1000)
                    
                else:
                    #start_location_name=co_ordinates_dict.keys()[i]
                    #end_location_name=co_ordinates_dict.keys()[j]
                    start_co=co_ordinates_dict.values()[i]
                    start_co=start_co.split(',')
                    start_co_lat=start_co[0]
                    start_co_lng=start_co[1]
                    end_co=co_ordinates_dict.values()[j]
                    end_co=end_co.split(',')
                    end_co_lat=end_co[0]
                    end_co_lng=end_co[1]    
        
                    lyft_cost_url="https://api.lyft.com/v1/cost?ride_type=lyft&start_lat="+start_co_lat+"&start_lng="+start_co_lng+"&end_lat="+end_co_lat+"&end_lng="+end_co_lng
                    lyft_cost_headers={'Authorization': "Bearer"+" "+access_lyft_token}
                    lyft_cost=requests.get(lyft_cost_url,headers=lyft_cost_headers)
                    
                    lyft_cost_data=lyft_cost.json()
                    lyft_cost_data=lyft_cost_data['cost_estimates']
                    #print lyft_cost_data
                    #print "lyft="
                    check=lyft_cost_data[0]['can_request_ride']
                    if not check:
                        #print "Entered"
                        String="\n Service not available for few Destinations "
                        lyftmatrix[i+1].append(10000)
                        continue
                    estimated_distance_miles= lyft_cost_data[0]['estimated_distance_miles']
                    print estimated_distance_miles
                    estimated_duration_seconds =lyft_cost_data[0]['estimated_duration_seconds']
                    estimated_duration_seconds=float(estimated_duration_seconds/60)    
                    print estimated_duration_seconds
                    max_cost=lyft_cost_data[0]['estimated_cost_cents_max']
                    max_cost=float(max_cost)/100
                    min_cost=lyft_cost_data[0]['estimated_cost_cents_min']
                    min_cost=float(min_cost)/100
                    lyft_cost=(max_cost+min_cost)/2
                    #cost_check_dict[start_location_name+end_location_name]=lyft_cost
                    lyftmatrix[i+1].append(lyft_cost)
                    lyftmatrix1[i+1].append(estimated_duration_seconds)
                    lyftmatrix2[i+1].append(estimated_distance_miles)
                    
                    
        if check_roundtrip:
            for i in range(1,location_counter+1):
                lyft_roundtrip[lyftmatrix[i][0]]=lyftmatrix[i][1]
                lyft_roundtrip_time[lyftmatrix1[i][0]]=lyftmatrix1[i][1]
                lyft_roundtrip_miles[lyftmatrix2[i][0]]=lyftmatrix2[i][1]          
        return
        
    def uber_cost(self):
        global location_counter
        global ubermatrix
        global co_ordinates_dict
        
        for i in range(0,location_counter):
            for j in range(0,location_counter):
                if i==j:
                    ubermatrix[i+1].append(1000)
                    ubermatrix1[i+1].append(1000)
                    ubermatrix2[i+1].append(1000)
                    
                else:
                    flag=0
                    start_co=co_ordinates_dict.values()[i]
                    start_co=start_co.split(',')
                    start_co_lat=start_co[0]
                    start_co_lng=start_co[1]
                    end_co=co_ordinates_dict.values()[j]
                    end_co=end_co.split(',')
                    end_co_lat=end_co[0]
                    end_co_lng=end_co[1]    
        
            
                    uber_cost_url="https://api.uber.com/v1.2/estimates/price?start_latitude="+start_co_lat+"&start_longitude="+start_co_lng+"&end_latitude="+end_co_lat+"&end_longitude="+end_co_lng
                    uber_cost_headers={'Authorization': "Token ydBbvAErXYq192-9DDuxq_5moV41Nw752LR2tTcQ"}
                    uber_cost=requests.get(uber_cost_url,headers=uber_cost_headers)
                    uber_cost_data=uber_cost.json()
                    ##print uber_cost_data
                    for p in range(0,len(uber_cost_data.keys())):
                        if uber_cost_data.keys()[p]=="code":
                            ubermatrix[i+1].append(10000)
                            flag=1
                        #if uber_cost_data['code']:
                        #return uber_cost_data['code']"""
                    if not flag:
                        uber_cost_data=uber_cost_data['prices']
                        for k in uber_cost_data:
                            uber_type=k.get('localized_display_name')
                            if uber_type=="uberX":
                                uber_estimate=k.get('estimate')
                                uber_duration=k.get('duration')
                                uber_duration=float(uber_duration)/60
                                uber_distance=k.get('distance')
                        uber_average=uber_estimate.split('-')
                        uber_min_cost=""
                        uber_max_cost=""
                        for k in uber_average[0]:
                            if k=="$":
                                pass
                            else:
                                uber_min_cost=uber_min_cost+k
                        for k in uber_average[1]:
                            uber_max_cost=uber_max_cost+k
                        uber_cost=(float(uber_max_cost)+float(uber_min_cost))/2
                        ubermatrix[i+1].append(uber_cost)
                        ubermatrix1[i+1].append(uber_duration)
                        ubermatrix2[i+1].append(uber_distance)
                    
        if check_roundtrip:
            for i in range(1,location_counter+1):
                uber_roundtrip[ubermatrix[i][0]]=ubermatrix[i][1]
                uber_roundtrip_time[ubermatrix1[i][0]]=ubermatrix1[i][1]
                uber_roundtrip_miles[ubermatrix2[i][0]]=ubermatrix2[i][1]
            
        return 
        
    def Djikstra(self):
        global lyft_string
        global location_counter
        global ubermatrix
        global lyftmatrix
        global co_ordinates_dict
        global uber_string
        global String
        global lyft_roundtrip_time
        global uber_roundtrip_time

        lyft_total_cost=0
        uber_total_cost=0
        lyft_path=""
        uber_path=""
        final_string=""
        counter=0
        column=1
        row=1
        min_value=1000
        interim_value=-1
        lyft_total_time=0
        lyft_total_miles=0
        uber_total_time=0
        uber_total_miles=0
        final_output={"providers":[]}
        
        
        #print "uber_string="
        #print uber_string
        
        #print "lyft string="
        #print lyft_string
        
        #print "lyftmatrix="
        #print lyftmatrix
        if lyft_string:
            lyft_path="Service not available in the specified area"
            lyft_total_cost=0.00
        else:
            while(counter<location_counter-1):
                for i in range(1,location_counter+1):
                    if min_value>lyftmatrix[row][i]:
                        min_value=lyftmatrix[row][i]
                        time=lyftmatrix1[row][i]
                        miles=lyftmatrix2[row][i]
                        interim_value=i
                if not lyft_path:
                    lyft_path=lyftmatrix[row][0]+","+lyftmatrix[0][interim_value]
                else:
                    lyft_path=lyft_path+","+lyftmatrix[0][interim_value]
                if min_value!=1000:
                    lyft_total_cost=lyft_total_cost+min_value
                    if time!=1000:
                        lyft_total_time=float(lyft_total_time)+float(time)
                    if miles!=1000:
                        lyft_total_miles=lyft_total_miles+miles
                for j in range(1,location_counter+1):
                    lyftmatrix[j][row]=1000
                column=row
                row=interim_value
                print "column="
                print column
                print "row="
                print row
                lyftmatrix[row][column]=1000
                min_value=1000
                counter=counter+1
                
                
        #print "lyft cost"
        #print lyft_total_cost
            if check_roundtrip:
                for i in range(0,location_counter):
                    if lyftmatrix[0][interim_value]==lyft_roundtrip.keys()[i]:
                        lyft_path=lyft_path+","+lyftmatrix[0][1]
                        lyft_total_cost=lyft_total_cost+lyft_roundtrip.values()[i]
                    
                    if lyftmatrix1[0][interim_value]==lyft_roundtrip_time.keys()[i]:
                         lyft_total_time=lyft_total_time+lyft_roundtrip_time.values()[i]

                    if lyftmatrix2[0][interim_value]==lyft_roundtrip_miles.keys()[i]:
                         lyft_total_miles=lyft_total_miles+lyft_roundtrip_miles.values()[i]        
                    
        counter=0
        column=1
        row=1
        min_value=1000
        interim_value=-1
        if uber_string:
            uber_path=uber_string
            uber_total_cost=0.00
            #print "uber="
            #print uber_string
        else:
            while(counter<location_counter-1):
                for i in range(1,location_counter+1):
                    if min_value>ubermatrix[row][i]:
                        min_value=ubermatrix[row][i]
                        ubertime=ubermatrix1[row][i]
                        ubermiles=ubermatrix2[row][i]
                        interim_value=i
                if not uber_path:
                    uber_path=ubermatrix[row][0]+","+ubermatrix[0][interim_value]
                else:
                    uber_path=uber_path+","+ubermatrix[0][interim_value]
                if min_value!=1000:
                    uber_total_cost=uber_total_cost+min_value
                    if ubertime!=1000:
                        uber_total_time=uber_total_time+ubertime
                    if ubermiles!=1000:
                        uber_total_miles=uber_total_miles+ubermiles    
                for j in range(1,location_counter+1):
                    ubermatrix[j][row]=1000
                column=row
                row=interim_value
                ubermatrix[row][column]=1000
                min_value=1000
                counter=counter+1
        #print "uber cost"
        #print uber_total_cost
            
            if check_roundtrip:
                for i in range(0,location_counter):
                    if ubermatrix[0][interim_value]==uber_roundtrip.keys()[i]:
                        uber_path=uber_path+","+ubermatrix[0][1]
                        uber_total_cost=uber_total_cost+uber_roundtrip.values()[i]

                    if ubermatrix1[0][interim_value]==uber_roundtrip_time.keys()[i]:
                        uber_total_time=uber_total_time+uber_roundtrip_time.values()[i]  
                    
                    if ubermatrix2[0][interim_value]==uber_roundtrip_miles.keys()[i]:
                        uber_total_miles=uber_total_miles+uber_roundtrip_miles.values()[i]   
                
                        
                        
        newstring={ "name" : "Uber",
            "total_costs_by_cheapest_car_type" : str(uber_total_cost),
            "currency_code": "USD",
            "total_duration" : str(uber_total_time),
            "duration_unit": "minute",
            "total_distance" : str(uber_total_miles),
            "distance_unit": "mile",
            "path": uber_path}   
        newstring1={"name" : "Lyft",
            "total_costs_by_cheapest_car_type" : str(lyft_total_cost),
            "currency_code": "USD",
            "total_duration" : str(lyft_total_time),
            "duration_unit": "minute",
            "total_distance" : str(lyft_total_miles),
            "distance_unit": "mile",
            "path": lyft_path}    
        finallist=[newstring,newstring1]
            
        final_string="By Lyft, Cost:"+str(lyft_total_cost)+"Time in Minutes:"+str(lyft_total_time)+"Distance in Miles"+str(lyft_total_miles)+"Path:"+lyft_path+"By Uber,Cost:"+str(uber_total_cost)+"Time in Minutes:"+str(uber_total_time)+"Distance in Miles"+str(uber_total_miles)+"Path:"+uber_path + String
        return finallist
     



if __name__ == '__main__':
	app.run(host='0.0.0.0',port=3000, debug=True)

