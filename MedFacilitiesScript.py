#Code to run script in Python3
#!/usr/bin/env python3

#Import Libraries
import requests, json, geopandas, subprocess, zipfile
import pandas as pd

#Location in DD, Earith, Centre of Cambridgeshire
#X_Loc = str(0.02)
#Y_Loc = str(52.35)

#Import Postcodes of Cambridgeshire
post_df = pd.read_csv("PCodes.csv")

#List of datasets #Have to input the geo lat long in each line below instead of using X_Loc and Y_Loc variables above
datasets = [
    {
        'filter': "OrganisationTypeID eq 'CLI'", #Clinics
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
    {
        'filter': "OrganisationTypeID eq 'DEN'", #Dentists
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
    {
        'filter': "OrganisationTypeID eq 'GPB'", #GPs
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
    {
        'filter': "OrganisationTypeID eq 'HOS'", #Hospitals
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
    {
        'filter': "OrganisationTypeID eq 'OPT'", #Opticians
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
    {
        'filter': "OrganisationTypeID eq 'PHA'", #Pharmacies
        'orderby': "geo.distance(Geocode, geography'POINT(0.02 52.35)')",
        'top': 1000,
        'skip': 0,
        'count': True
    },
#Add more datasets as needed
]

#Create empty list of Dataframes
df_list = []

#Import Data from NHS Digital
for dataset in datasets:
    response = requests.request(
        method='POST',
        url='https://api.nhs.uk/service-search/search?api-version=1',
        headers={
            'Content-Type': 'application/json',
            'subscription-key': '557d555fd712449f894e78e50a460000'
        },
        json=dataset
    )

    #Parse the response as JSON
    data = response.json()

    #Extract the required data from the JSON response
    output = []
    for item in data.get('value', []):
        output.append([
            item.get('OrganisationID'),
            item.get('NACSCode'),
            item.get('OrganisationName'),
            item.get('OrganisationType'),
            item.get('Postcode'),
            item.get('URL'),        
            item.get('Address1'),
            item.get('Address2'),
            item.get('Address3'),
            item.get('City'),
            item.get('County'),
            item.get('Latitude'),
            item.get('Longitude'),
            item.get('ServicesProvided'),
            item.get('OpeningTimes'),
            item.get('Contacts'),
            item.get('LastUpdatedDate'),
        ])
    columns = ['OrgID', 'OCS_Code', 'OrgName', 'OrgType', 'Postcode', 'URL', 'Address1', 'Address2', 'Address3', 'City', 'County', 'Latitude', 'Longitude', 'ServicesProvided', 'OpeningTimes', 'Contacts', 'LastUpdate']
    df=pd.DataFrame(output, columns=columns)
    df_list.append(df)

#Combined all DFs into single DF
all_df = pd.concat(df_list, ignore_index=True)

#Removes all locations outside of Cambridgeshire
cambs_df = pd.merge(all_df, post_df, on='Postcode')

#Extracts the phone number from the Contacts field
phone_df = cambs_df['Contacts'].str.split(',', expand=True)
phone_df = phone_df[[3]]
phone_df.columns = ['Phone']
phone_df.dropna(inplace=True)
phone_df['Phone'] = phone_df['Phone'].map(lambda x: ''.join([i for i in x if i.isdigit()]))
cambs_df = pd.concat([cambs_df, phone_df], axis=1)
del_col = ['Contacts']
cambs_df.drop(del_col, axis=1, inplace=True)

#Creation of Services Dataframe
services_df = cambs_df.copy()
del_col = ['OCS_Code',
       'Postcode', 'URL', 'Address1', 'Address2', 'Address3', 'City', 'County', 'OpeningTimes', 'LastUpdate']
services_df.drop(del_col, axis=1, inplace=True)
services_df = services_df[services_df['ServicesProvided'].apply(lambda x: x != [])]
services_df = services_df.explode('ServicesProvided').reset_index(drop=True)
services_df.rename(columns={'ServicesProvided': 'Services'}, inplace=True)

#Creation of Opening Times Dataframe
times_df = cambs_df.copy()
del_col = ['OCS_Code',
   'Postcode', 'URL', 'Address1', 'Address2', 'Address3', 'City', 'County', 'ServicesProvided', 'LastUpdate']
times_df.drop(del_col, axis=1, inplace=True)
times_df = times_df[times_df['OpeningTimes'].apply(lambda x: x != None)]
times_df['OpeningTimes'] = times_df['OpeningTimes'].apply(json.loads)
times_df = times_df.explode('OpeningTimes').reset_index(drop=True)
times_df = pd.concat([times_df[['OrgID', 'OrgName', 'OrgType', 'Phone', 'Latitude', 'Longitude']].reset_index(drop=True), pd.json_normalize(times_df['OpeningTimes'])], axis=1)
del_col =['OpeningTimeType', 'AdditionalOpeningDate', 'IsOpen']
times_df.drop(del_col, axis=1, inplace=True)
times_df = times_df.rename(columns={'OffsetOpeningTime': 'OpenTime', 'OffsetClosingTime': 'CloseTime'})

#Updates Cambs Dataframe
del_col = ['OpeningTimes', 'ServicesProvided']
cambs_df.drop(del_col, axis=1, inplace=True)

#Creation of GeoDataframes
cambs_gdf = geopandas.GeoDataFrame(
    cambs_df, geometry=geopandas.points_from_xy(cambs_df.Longitude, cambs_df.Latitude), crs="EPSG:4326")

times_gdf = geopandas.GeoDataFrame(
    times_df, geometry=geopandas.points_from_xy(times_df.Longitude, times_df.Latitude), crs="EPSG:4326")

services_gdf = geopandas.GeoDataFrame(
    services_df, geometry=geopandas.points_from_xy(services_df.Longitude, services_df.Latitude), crs="EPSG:4326")

#Creation of CSV files from original Dataframes
times_df.to_csv("times.csv")
services_df.to_csv("services.csv")
cambs_df.to_csv("cambs.csv")

#Creation of Shapefiles from GeoDataframes
cambs_gdf.to_file('Cambs.shp', driver='ESRI Shapefile')
services_gdf.to_file('Services.shp', driver='ESRI Shapefile')
times_gdf.to_file('Times.shp', driver='ESRI Shapefile')

#Creation of Zipfiles
filenames = ['Cambs.shp', 'Cambs.dbf', 'Cambs.prj', 'Cambs.shx']
with zipfile.ZipFile("Cambs.zip", mode="w") as archive:
	for filename in filenames:
		archive.write(filename)

filenames = ['Times.shp', 'Times.dbf', 'Times.prj', 'Times.shx']
with zipfile.ZipFile("Times.zip", mode="w") as archive:
        for filename in filenames:
                archive.write(filename)

filenames = ['Services.shp', 'Services.dbf', 'Services.prj', 'Services.shx']
with zipfile.ZipFile("Services.zip", mode="w") as archive:
        for filename in filenames:
                archive.write(filename)

#Emails zip files to my email address
subprocess.run("mutt -s 'AGOL update' xxx@gmail.com -a Cambs.zip -a Times.zip -a Services.zip < myfile.txt", shell=True)

print("Alles gemacht!")
