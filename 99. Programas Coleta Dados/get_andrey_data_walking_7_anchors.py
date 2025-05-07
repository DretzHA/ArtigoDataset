import asyncio
import asyncpg
from dotenv import load_dotenv
import sys
import csv
import json
from datetime import datetime, timezone

conn_pool = None
final_data = []

def write_list_to_txt(final_data, filename):
    try:
        # Open the file in write mode and write the list to itMOV_MIP_4T_V1
        with open(filename, 'w') as file:
            for sub_lista in final_data:
                line = ','.join(map(str, sub_lista))
                file.write(line + '\n')
        print(f"List successfully written to '{filename}'")
    except IOError:
        print(f"An error occurred while writing to the file '{filename}'")

def track_route(initial_time, actual_time):
    
    time_lapse = 5 #Define the range (in seconds) to be used as a reference, this is equivalent of the time standing up in each point of the route
    
    dif_sec = actual_time - initial_time 

    #This conditionals sentences fraction the portion relative to each position, and avoid problemns came from more than one sample with the same time as the previous.
    #Furthermore, this help us on the cases that there are loss of samples throght the time.

    #CASO DA ROTA EM 'M'
    if dif_sec < time_lapse: #P1 corredor 1
        track_x = -1.14 
        track_y = 0.39 
        track_z = 1.81  
    elif dif_sec >= time_lapse and dif_sec < (2 * time_lapse): #P2 corredor 1
        track_x = -2.34 
        track_y = 0.39
        track_z = 1.81  
    elif dif_sec >= (2 * time_lapse) and dif_sec < (3 * time_lapse): #P3 corredor 1
        track_x = -3.54 
        track_y = 0.39
        track_z = 1.81  
    elif dif_sec >= (3 * time_lapse) and dif_sec < (4 * time_lapse): #P4 corredor 1
        track_x = -4.74 
        track_y = 0.39 
        track_z = 1.81  
    elif dif_sec >= (4 * time_lapse) and dif_sec < (5 * time_lapse): #P5 corredor 1
        track_x = -5.94 
        track_y = 0.39 
        track_z = 1.81  
    elif dif_sec >= (5 * time_lapse) and dif_sec < (6 * time_lapse): #PF
        track_x = -7.14 
        track_y = 0.84 
        track_z = 1.81  
    elif dif_sec >= (6 * time_lapse) and dif_sec < (7 * time_lapse): #PE
        track_x = -7.14 
        track_y = 2.04 
        track_z = 1.81  
    elif dif_sec >= (7 * time_lapse) and dif_sec < (8 * time_lapse): #PD
        track_x = -7.14 
        track_y = 3.24 
        track_z = 1.81 
    elif dif_sec >= (8 * time_lapse) and dif_sec < (9 * time_lapse): #PC
        track_x = -7.14 
        track_y = 4.44 
        track_z = 1.81      
    elif dif_sec >= (9 * time_lapse) and dif_sec < (10 * time_lapse): #P5 corredor 2 
        track_x = -5.94 
        track_y = 4.44 
        track_z = 1.81  
    elif dif_sec >= (10 * time_lapse) and dif_sec < (11 * time_lapse): #P4 corredor 2 
        track_x = -4.74 
        track_y = 4.44 
        track_z = 1.81  
    elif dif_sec >= (11 * time_lapse) and dif_sec < (12 * time_lapse): #P3 corredor 2 
        track_x = -3.54 
        track_y = 4.44
        track_z = 1.81  
    elif dif_sec >= (12 * time_lapse) and dif_sec < (13 * time_lapse): #P2 corredor 2 
        track_x = -2.34 
        track_y = 4.44 
        track_z = 1.81  
    elif dif_sec >= (13 * time_lapse) and dif_sec < (14 * time_lapse): #P1 corredor 2
        track_x = -1.14 
        track_y = 4.44 
        track_z = 1.81  
    elif dif_sec >= (14 * time_lapse) and dif_sec < (15 * time_lapse): #P2 corredor 2
        track_x = -2.34
        track_y = 4.44
        track_z = 1.81  
    elif dif_sec >= (15 * time_lapse) and dif_sec < (16 * time_lapse): #P3 corredor 2
        track_x = -3.54 
        track_y = 4.44
        track_z = 1.81  
    elif dif_sec >= (16 * time_lapse) and dif_sec < (17 * time_lapse): #P4 corredor 2
        track_x = -4.74 
        track_y = 4.44 
        track_z = 1.81 
    elif dif_sec >= (17 * time_lapse) and dif_sec < (18 * time_lapse): #P5 corredor 2
        track_x = -5.94 
        track_y = 4.44 
        track_z = 1.81  
    elif dif_sec >= (18 * time_lapse) and dif_sec < (19 * time_lapse): #PC
        track_x = -7.14 
        track_y = 4.444 
        track_z = 1.81 
    elif dif_sec >= (19 * time_lapse) and dif_sec < (20 * time_lapse): #PB
        track_x = -7.14
        track_y = 5.64 
        track_z = 1.81 
    elif dif_sec >= (20 * time_lapse) and dif_sec < (21 * time_lapse): #PA
        track_x = -7.14
        track_y = 6.84 
        track_z = 1.81  
    elif dif_sec >= (21 * time_lapse) and dif_sec < (22 * time_lapse): #P5 corredor 3
        track_x = -5.94
        track_y = 6.84 
        track_z = 1.81  
    elif dif_sec >= (22 * time_lapse) and dif_sec < (23 * time_lapse): #P4 corredor 3
        track_x = -4.74 
        track_y = 6.84 
        track_z = 1.81  
    elif dif_sec >= (23 * time_lapse) and dif_sec < (24 * time_lapse): #P3 corredor 3
        track_x = -3.54 
        track_y = 6.84 
        track_z = 1.81  
    elif dif_sec >= (24 * time_lapse) and dif_sec < (25 * time_lapse): #P2 corredor 3
        track_x = -2.34 
        track_y = 6.84 
        track_z = 1.81  
    else: #dif_sec >= (25 * time_lapse) and dif_sec < (26 * time_lapse): #P1 corredor 3
        track_x = -1.14 
        track_y = 6.84 
        track_z = 1.81  
    # else:
    #     return
    return track_x, track_y, track_z

async def create_pool():
    global conn_pool
    if conn_pool == None:
        conn_pool = await asyncpg.create_pool()    

async def print_tests():
    
    async with conn_pool.acquire() as connection:                                            
        # Open a transaction.
        async with connection.transaction():                                


            result = await connection.fetch('''
                SELECT * from sigivest.test_annotations order by start_time desc;
                ''')
            
    for record in result:
        print(f''' {record['test_name']}   {record['start_time']}  {record['end_time']}  {record['description']}''')

    return result

async def get_Andrey_tests_with_position(test_name): 

    filename = "exported_" + test_name + ".txt" 
    flag = True
    async with conn_pool.acquire() as connection:                                            
        # Open a transaction.
        async with connection.transaction():   
            #select all ppes that were seen in this test
            table = await connection.fetch('''
            SELECT 
                b.idbeacon,    
                MAX(CASE WHEN a.idarray_coordinate = 'd540b276-ed5f-11ef-a35b-0242ac120003' THEN a.rssi_dbm END) AS rssi_7,
                MAX(CASE WHEN a.idarray_coordinate = '07e6f7ee-e7e8-11ef-b979-0242ac120004' THEN a.rssi_dbm END) AS rssi_6,
                MAX(CASE WHEN a.idarray_coordinate = 'dbd008d0-ed5f-11ef-a35b-0242ac120003' THEN a.rssi_dbm END) AS rssi_5,                 
                MAX(CASE WHEN a.idarray_coordinate = '9055c740-ff71-11ef-b668-0242ac120009' THEN a.rssi_dbm END) AS rssi_4,
                MAX(CASE WHEN a.idarray_coordinate = '9055ab34-ff71-11ef-b668-0242ac120009' THEN a.rssi_dbm END) AS rssi_3,
                MAX(CASE WHEN a.idarray_coordinate = '9055c7cc-ff71-11ef-b668-0242ac120009' THEN a.rssi_dbm END) AS rssi_2,
                MAX(CASE WHEN a.idarray_coordinate = '9055c790-ff71-11ef-b668-0242ac120009' THEN a.rssi_dbm END) AS rssi_1,
                MAX(CASE WHEN a.idarray_coordinate = 'd540b276-ed5f-11ef-a35b-0242ac120003' THEN (aoa.arrival_angle_rad).alpha END) AS az_7,
                MAX(CASE WHEN a.idarray_coordinate = '07e6f7ee-e7e8-11ef-b979-0242ac120004' THEN (aoa.arrival_angle_rad).alpha END) AS az_6,
                MAX(CASE WHEN a.idarray_coordinate = 'dbd008d0-ed5f-11ef-a35b-0242ac120003' THEN (aoa.arrival_angle_rad).alpha END) AS az_5,
                MAX(CASE WHEN a.idarray_coordinate = '9055c740-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).alpha END) AS az_4,
                MAX(CASE WHEN a.idarray_coordinate = '9055ab34-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).alpha END) AS az_3,
                MAX(CASE WHEN a.idarray_coordinate = '9055c7cc-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).alpha END) AS az_2,
                MAX(CASE WHEN a.idarray_coordinate = '9055c790-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).alpha END) AS az_1,
                MAX(CASE WHEN a.idarray_coordinate = 'd540b276-ed5f-11ef-a35b-0242ac120003' THEN (aoa.arrival_angle_rad).gamma END) AS el_7,
                MAX(CASE WHEN a.idarray_coordinate = '07e6f7ee-e7e8-11ef-b979-0242ac120004' THEN (aoa.arrival_angle_rad).gamma END) AS el_6,
                MAX(CASE WHEN a.idarray_coordinate = 'dbd008d0-ed5f-11ef-a35b-0242ac120003' THEN (aoa.arrival_angle_rad).gamma END) AS el_5,
                MAX(CASE WHEN a.idarray_coordinate = '9055c740-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).gamma END) AS el_4,
                MAX(CASE WHEN a.idarray_coordinate = '9055ab34-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).gamma END) AS el_3,
                MAX(CASE WHEN a.idarray_coordinate = '9055c7cc-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).gamma END) AS el_2,
                MAX(CASE WHEN a.idarray_coordinate = '9055c790-ff71-11ef-b668-0242ac120009' THEN (aoa.arrival_angle_rad).gamma END) AS el_1,
                MAX((ppec.coordinate_m).x) AS x,
                MAX((ppec.coordinate_m).y) AS y,
                MAX((ppec.coordinate_m).z) AS z,
                b.create_time,
                b.bluetooth_channel,
                b.idppe 
            FROM 
                sigivest.beacons b
            LEFT JOIN 
                sigivest.arrivals a ON b.idbeacon = a.idbeacon
            LEFT JOIN 
                sigivest.angle_of_arrivals aoa ON aoa.idarrival = a.idarrival
            LEFT JOIN
                sigivest.ppe_coordinates ppec ON (ppec.metadata->>'beacon_uuid')::uuid = b.idbeacon
            WHERE
                b.create_time >= (select start_time from sigivest.test_annotations where test_name = $1) 
            AND
                b.create_time <= (select end_time from sigivest.test_annotations where test_name = $1)
            AND a.idarray_coordinate IN (
                    'd540b276-ed5f-11ef-a35b-0242ac120003',
                    '07e6f7ee-e7e8-11ef-b979-0242ac120004',
                    'dbd008d0-ed5f-11ef-a35b-0242ac120003',
                    '9055c740-ff71-11ef-b668-0242ac120009',
                    '9055ab34-ff71-11ef-b668-0242ac120009',
                    '9055c7cc-ff71-11ef-b668-0242ac120009',
                    '9055c790-ff71-11ef-b668-0242ac120009'         
                )
            GROUP BY 
                b.idbeacon
            ORDER BY 
                b.create_time;                  
                ''', test_name) 
                    #b.create_time BETWEEN '2024-09-23 17:30:00.00 -0300' AND '2024-09-23 17:30:20 -0300'
                                        
            for data in table:
                # create_time = angle['create_time']
                # alpha_rad = angle['arrival_angle_rad']['alpha']
                # gamma_rad = angle['arrival_angle_rad']['gamma']
                # i_array = angle['i_array']
                # q_array = angle['q_array']
                        
                #useful_data = {}
                #useful_data.update({'gamma_rad': angle['arrival_angle_rad']['gamma']})
                #useful_data.update({'alpha_rad': angle['arrival_angle_rad']['alpha']})
                #useful_data.update({'rssi_dbm': angle['rssi_dbm']})
                #useful_data.update({'i_array': angle['i_array']})
                #useful_data.update({'q_array': angle['q_array']})
                #angle_series.update({str(angle['create_time']): useful_data})
                        
                if str(data['idppe']) != 0: #Filter the only TAG tha we want #tag thiago 2c08d2cc-7a1c-9d34-25ea-6265acb43d72
                    useful_data = []
                    if flag:
                        initial_time = float(data['create_time'].timestamp()) #Set the first timestamp to be the reference at the track_route function
                        flag = False

                    real_x, real_y, real_z = track_route(initial_time, float(data['create_time'].timestamp())) #Return the real position when the TAG is in moviment
                    result = track_route(initial_time, float(data['create_time'].timestamp()))
                    if result is not None:
                        real_x, real_y, real_z = result
                    else:
                    # Tratar o caso em que track_route retorna None
                        real_x = 'Nan'
                        real_y = 'Nan'
                        real_z = 'Nan'

                    # real_x = -8.34
                    # real_y = 4.74
                    # real_z = 1.65

                    useful_data.append(str(data['create_time'].timestamp()))
                    useful_data.append(str(data['idppe']))
                    useful_data.append(str(data['idbeacon']))
                    useful_data.append(data['bluetooth_channel'])
                    useful_data.append(float(data['rssi_1'] if data['rssi_1'] else 'NaN')) 
                    useful_data.append(float(data['rssi_2'] if data['rssi_2'] else 'NaN'))
                    useful_data.append(float(data['rssi_3'] if data['rssi_3'] else 'NaN'))
                    useful_data.append(float(data['rssi_4'] if data['rssi_4'] else 'NaN'))
                    useful_data.append(float(data['rssi_5'] if data['rssi_5'] else 'NaN'))
                    useful_data.append(float(data['rssi_6'] if data['rssi_6'] else 'NaN'))
                    useful_data.append(float(data['rssi_7'] if data['rssi_7'] else 'NaN'))
                    useful_data.append(float(data['az_1'] if data['az_1'] else 'NaN'))
                    useful_data.append(float(data['az_2'] if data['az_2'] else 'NaN'))
                    useful_data.append(float(data['az_3'] if data['az_3'] else 'NaN'))
                    useful_data.append(float(data['az_4'] if data['az_4'] else 'NaN'))
                    useful_data.append(float(data['az_5'] if data['az_5'] else 'NaN'))
                    useful_data.append(float(data['az_6'] if data['az_6'] else 'NaN'))
                    useful_data.append(float(data['az_7'] if data['az_7'] else 'NaN'))
                    useful_data.append(float(data['el_1'] if data['el_1'] else 'NaN'))
                    useful_data.append(float(data['el_2'] if data['el_2'] else 'NaN'))
                    useful_data.append(float(data['el_3'] if data['el_3'] else 'NaN')) 
                    useful_data.append(float(data['el_4'] if data['el_4'] else 'NaN'))
                    useful_data.append(float(data['el_5'] if data['el_5'] else 'NaN'))
                    useful_data.append(float(data['el_6'] if data['el_6'] else 'NaN'))
                    useful_data.append(float(data['el_7'] if data['el_7'] else 'NaN'))
                    useful_data.append(float(data['x'] if data['x'] else 'NaN'))
                    useful_data.append(float(data['y'] if data['y'] else 'NaN'))
                    useful_data.append(float(data['z'] if data['z'] else 'NaN'))
                    useful_data.append(float(real_x))
                    useful_data.append(float(real_y))
                    useful_data.append(float(real_z)) 

                    final_data.append(useful_data)
                
    write_list_to_txt(final_data, filename)                
  
async def main(test_name):    

    await create_pool()
      
    await get_Andrey_tests_with_position(test_name)
    
if __name__ == "__main__":    
    if len(sys.argv) < 2:
        print("No test name was provided. Returning...")
        exit()
    else:
        test_name = sys.argv[1]
    load_dotenv()
    asyncio.run(main(test_name))    