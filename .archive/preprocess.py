import numpy as np
import pandas as pd
import json
#Imports Libraries

file_path = "10.08.2025 Cheri pulley"
file = open("data/" + file_path + ".txt", "r")
lines = file.readlines()
#Read everything in the data file into lines
#lines is a list, each element is one line in the data file


i = 0
while lines[i] != "4) Trace Data\n":
    i += 1
i += 2
#Finds where the raw data starts
#Skips the two blank lines at very beginging


raw_data = []
for j in range(i, len(lines)):
    line = lines[j]
    bloodflow_val = float(line.split("\t")[4])
    raw_data.append(bloodflow_val)
# Example of line: 720  0   11   59   21.8     0.0
# Extacts the blood perfusion(Which is value on index 4), in this case 21.8
# Appends all blood perfusion into raw_data list


points = ["outergate", "hand3mile", "hand5mile"]
activities = ["baseline", "0lbs", "5lbs", "10lbs"]
# Define Variables used in this experiment


times = pd.DataFrame(index = ["baseline", "0lbs", "5lbs", "10lbs"], 
                    columns = ["outergate", "hand3mile", "hand5mile"])
times['outergate']['baseline'] = (60, 120) #1 - 60
times['outergate']['0lbs'] = (120, 180) #61 - 120
times['outergate']['5lbs'] = (180, 240) #121 - 180
times['outergate']['10lbs'] = (240, 300) #181 - 240
times['hand3mile']['baseline'] = (360, 420) #241-300
times['hand3mile']['0lbs'] = (420, 480) #301 - 361
times['hand3mile']['5lbs'] = (480, 540) #461 - 
times['hand3mile']['10lbs'] = (540, 600)
times['hand5mile']['baseline'] = (660, 720)
times['hand5mile']['0lbs'] = (720, 780)
times['hand5mile']['5lbs'] = (780, 840) 
times['hand5mile']['10lbs'] = (840, 900)

# Create Pandas Table(Times) to store all the time intervals
# Hard Coded because time intervals could vary from experiment to experiment due to errors
# Errors like accidently failing to stop the machine on time(in this case it happend during 243)

class CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, (list, tuple)):
            # Format arrays/lists on a single line
            return '[' + ', '.join(json.dumps(item) for item in obj) + ']'
        elif isinstance(obj, dict):
            # Handle dictionaries with proper indentation
            items = []
            for key, value in obj.items():
                formatted_value = self.encode(value)
                items.append(f'"{key}": {formatted_value}')
            return '{\n' + ',\n'.join(items) + '\n}'
        else:
            return super().encode(obj)

data = {}
data['outergate'] = {}
data['hand3mile'] = {}
data['hand5mile'] = {}
for i in points:
    for j in activities:
        slice_range = times[i][j]
        data[i][j] = raw_data[slice_range[0] : slice_range[1]]
json_string = json.dumps(data, cls=CustomJSONEncoder, indent=4)
for i in points:
    for j in activities:
        print(len(data[i][j]))
print(json_string)

# Create Pandas Table(data) to store all data
# Slice the Corresponding intervals from raw_data based on values from Times table
# Store all the data as arrays into corresponding cells
# np_data = data.to_numpy()
# np_data = np_data.flatten()
# np_data = np_data.tolist()
# np_data = np.array(np_data)

#Save after running