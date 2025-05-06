import os
import json
import asyncio
import asyncpg
import pandas as pd
import paho.mqtt.client as mqtt
import threading
import time
import numpy as np
from dotenv import load_dotenv
from datetime import timedelta

# Global variables
data_anchors = []
data_positions = []
data_timeouts = []
is_collecting = False
exit_program = False
conn_pool = None
real_x = np.nan
real_y = np.nan
real_z = np.nan
test_created = False  # New flag to track if the test has been created in the database
test_timeout = 180 # test duration after receiveing the first beacon
start_countdown = False
countdown_thread = None

# Global lock for synchronizing the update of real_x, real_y, real_z
real_coordinates_lock = threading.Lock()

# Countdown logic
def countdown_to_stop():
    global is_collecting, exit_program
    remaining_time = test_timeout
    while remaining_time > 0 and not exit_program:
        #print(f"Time remaining: {remaining_time} seconds")
        time.sleep(1)
        remaining_time -= 1
    if remaining_time == 0:
        print("Timeout reached. Stopping data collection.")
        is_collecting = False
        exit_program = True


# Database setup
async def create_pool():
    global conn_pool
    if conn_pool is None:
        conn_pool = await asyncpg.create_pool()

async def start_test_in_db(test_name, description):
    async with conn_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM sigivest.test_annotations WHERE test_name = $1",
                test_name,
            )
            result = await connection.fetchrow(
                """
                INSERT INTO sigivest.test_annotations (test_name, description, start_time)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                RETURNING *;
                """,
                test_name,
                description,
            )
    return result

async def end_test_in_db(test_name):
    async with conn_pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE sigivest.test_annotations
            SET end_time = CURRENT_TIMESTAMP
            WHERE test_name = $1;
            """,
            test_name,
        )

# MQTT Callbacks
def on_connection(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect: {rc}")

def on_message(client, userdata, message):
    global is_collecting, real_x, real_y, real_z, countdown_thread, start_countdown
    if is_collecting:
        topic_parts = message.topic.split('/')
        if message.topic.startswith("silabs/aoa/angle_and_iq_report"):
            anchor_id = topic_parts[3]
            ppe_id = topic_parts[-1]
            angles_dict = json.loads(message.payload)
            with real_coordinates_lock:
                # Update message with current real coordinates
                angles_dict.update(
                    {'receive_time': pd.Timestamp.now(), 'anchor_id': anchor_id, 'ppe_id': ppe_id,
                     'x_real': real_x, 'y_real': real_y, 'z_real': real_z}
                )
            data_anchors.append(angles_dict)
        elif message.topic.startswith("silabs/aoa/position"):
            ppe_id = topic_parts[-1]
            position_dict = json.loads(message.payload)
            position_dict.update(
                {'receive_time': pd.Timestamp.now(), 'ppe_id': ppe_id}
            )
            data_positions.append(position_dict)

        elif message.topic.startswith("silabs/timeouts/data"):
            ppe_id = topic_parts[-1]
            anchor_id = topic_parts[-2]
            timeouts_dict = json.loads(message.payload)
            create_time_unix = (
                pd.to_datetime(pd.Timestamp.now())  # Convert to datetime
                + timedelta(hours=3)  # Add 3 hours
                ).timestamp()  # Convert to Unix timestamp
            
            timeouts_dict.update(
                {'receive_time': create_time_unix, 'ppe_id': ppe_id, 'anchor_id': anchor_id}
            )
            data_timeouts.append(timeouts_dict)

        # Start the countdown thread on the first received message
        if not start_countdown:
            start_countdown = True
            countdown_thread = threading.Thread(target=countdown_to_stop, daemon=True)
            countdown_thread.start()


# Toggle data collection
def toggle_data_collection():
    global is_collecting, exit_program, real_x, real_y, real_z, test_created
    aux_collecting = is_collecting
    while True:
        user_input = input('Press Enter to Start/Stop collection. Type "exit" to quit.\n')
        if user_input == '':
          #  is_collecting = not is_collecting
            aux_collecting = not aux_collecting
            if aux_collecting:
                # Prompt for real x, y, z values and update
                try:
                    real_x = float(input("Enter real X coordinate: "))
                    real_y = float(input("Enter real Y coordinate: "))
                    real_z = float(input("Enter real Z coordinate: "))
                    is_collecting = True
                except ValueError:
                    print("Invalid input. Please enter numerical values.")
                    real_x, real_y, real_z = np.nan, np.nan, np.nan 
            else:
                is_collecting = False
            print(f"Data collection {'started' if is_collecting else 'stopped'}.")
                
        elif user_input.lower() == 'exit':
            exit_program = True
            break

# Create DataFrame
def create_dataframe(df_anchors, df_positions):
    global real_x, real_y, real_z

    anchor_mapping = {
        'ble-pd-0C4314F469CC': 4,
        'ble-pd-0C4314F46B26': 3,
        'ble-pd-0C4314F46B3F': 2,
        'ble-pd-0C4314F46CC2': 1,
        'ble-pd-C299A0EB1D6C' : 5,
        'ble-pd-D299A0EB1D6C' : 7,
        'ble-pd-639AA0EB1D6C' : 6

    }
    rows = []
    df_merged = pd.merge(
        df_anchors, df_positions[['sequence', 'ppe_id', 'x', 'y', 'z']], on=['sequence', 'ppe_id'], how='left'
    )
    grouped = df_merged.groupby(['sequence', 'ppe_id'])
    for (sequence, ppe_id), group in grouped:
        create_time_unix = (
        pd.to_datetime(group['receive_time'].iloc[0])  # Convert to datetime
        + timedelta(hours=3)  # Add 3 hours
        ).timestamp()  # Convert to Unix timestamp
        
        row = {
            'CreateTime': create_time_unix,
            'ppeID': ppe_id,
            'BeaconID': sequence,
            'Channel': group['channel'].iloc[0],
            **{f'RSSI_{i+1}': np.nan for i in range(7)},
            **{f'Azim_{i+1}': np.nan for i in range(7)},
            **{f'Elev_{i+1}': np.nan for i in range(7)},
            'X_sylabs': group['x'].iloc[0],
            'Y_sylabs': group['y'].iloc[0],
            'Z_sylabs': group['z'].iloc[0],
            'X_real': group['x_real'].iloc[0],
            'Y_real': group['y_real'].iloc[0],
            'Z_real': group['z_real'].iloc[0]
        }
        for _, anchor_data in group.iterrows():
            anchor_id = anchor_data['anchor_id']
            if anchor_id in anchor_mapping:
                idx = anchor_mapping[anchor_id]
                row[f'RSSI_{idx}'] = anchor_data['rssi']
                row[f'Azim_{idx}'] = np.radians(anchor_data['azimuth'])
                row[f'Elev_{idx}'] = np.radians(anchor_data['elevation'])
        rows.append(row)
    return pd.DataFrame(rows)

# Main function
async def main():
    global is_collecting
    
    load_dotenv()
    await create_pool()

    test_name = input("Enter test name: ")
    description = input("Enter test description: ")

    test_record = await start_test_in_db(test_name, description)

    client = mqtt.Client(client_id="MQTT_Test_Manager", clean_session=True)
    client.on_connect = on_connection
    client.on_message = on_message
    client.connect("103.0.1.31")
    client.subscribe("silabs/aoa/angle_and_iq_report/+/#")
    client.subscribe("silabs/aoa/position/positioning-LabSC/#")
    client.subscribe("silabs/timeouts/data/periodic_sync_report/+/#")
    client.loop_start()

    toggle_thread = threading.Thread(target=toggle_data_collection, daemon=True)
    toggle_thread.start()

    try:
        while not exit_program:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

        await end_test_in_db(test_name)

        if data_anchors and data_positions:
            df_anchors = pd.DataFrame(data_anchors)
            df_positions = pd.DataFrame(data_positions)
            final_df = create_dataframe(df_anchors, df_positions)
            final_df.to_csv(f"Datasets/Calibration/{test_name}_data.csv", index=False)
            print(f"Data saved to {test_name}_data.csv")

        df_timeouts = pd.DataFrame(data_timeouts)
        # df_timeouts.to_csv(f"Datasets/Timeouts/{test_name}_data.csv", index=False)
        print("Program exited.")

if __name__ == "__main__":
    asyncio.run(main())
