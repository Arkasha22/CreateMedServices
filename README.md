# CreateMedServices
Create Medical Services Shapefile

Process Followed

1 – Had to create a new Postcodes file in order to act as a filter for Cambridgeshire.

2 – Changed the co-ordinates for my NHS facilities API.

3 – Combined all the required datasets into a single pandas dataframe (Clinics, Dentists, GPs, Hospitals, Opticians, Pharmacies).
4 – Pulled out the contact phone number from the Contacts field, which contained phone numbers, fax numbers, websites etc.
5 – Created a new dataframe and extracted the services, which were originally in a wide format into a long format. This increases the data size, but makes it easier to filter by service type.
6 – Created a new dataframe and extracted the opening times, from a wide format into a long format.
7 – Used the geopandas library to create a geodataframe from a normal dataframe.
8 – Created a shapefile for each geodataframe.
9 – Zipped the shapefile files for easier use.
10 – Emailed the zipped shapefiles for myself so that I can upload them to AGOL.
