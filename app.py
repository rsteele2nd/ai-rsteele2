from flask import Flask, jsonify, render_template, request, redirect, url_for
import os
import openai
import plotly.express as px
import pandas as pd
import json
import plotly
import csv
import io
import time

app = Flask(__name__)

# Load OpenAI API key from environment variable
openai.api_key = ""

# In-memory data storage
data = {
    "activities": [],
    "equipment": [],
    "constraints": [],
    "workflows": [],
    "schedule": {
        "startDate": None,
        "startTime": None
    },
    "message" : """You are a scheduling agent for the batches and associated workflows that I give you.
     
    I have multiple batch ids which have an associated workflow outlined in the provided JSON data, involving the use of shared equipment in a 
    factory setting. Using the start time provided in the JSON block, create an optimized schedule that maximizes equipment usage from the 
    starting time and runs the processes as fast as possible, NEVER letting the equipment be idle unless a constraint requires it or 
    there are no more batches to run. If a piece of equipment becomes available and there's another batch to run, START THE BATCH. 
    We are looking to maximize concurrency and WE WANT PARALLEL BATCH EXECUTION. As soon as one part of a workflow finishes with a 
    piece of equipment, it's available for the next batch with that piece of equipment in its workflow. THIS IS OPTIMIZED IF the 
    equipment is continuously running and the schedule isn't necessarily completing one entire workflow before starting another. Base 
    the start and end times for each part of the workflow on the equipment use duration provided. The duration given is in minutes.

    IMPORTANT THAT When you calculate this keep track of whether each piece of equipment is free or being used and as soon as it's free, look
    to schedule another batch with that piece of equipment as soon as possible. MAXIMIZE EQUIPMENT USAGE 

    PLEASE RETURN the name of the activity as "Batch ID (Workflow Equipment)" 

    IT IS NOT NECESSARY FOR A BATCH TO BE COMPLETE BEFORE ANOTHER BATCH STARTS 
    PLEASE PAY ATTENTION TO THE WORKFLOWS. IF A BATCH WORKFLOW DOESN'T HAVE A PIECE OF EQUIPMENT IN IT THEN THERE SHOULDN'T BE 
    AN ACTIVITY ON THAT MACHINE WITH THAT BATCH ID. A piece of equipment can only be used by one batch at a time. 
    """
}

demo_data = {
    'activities': [
        {'id': 1701805532530, 'name': 'Cookie Batch', 'workflow': ['Workflow 1']},
        {'id': 1701805535459, 'name': 'Cookie Batch', 'workflow': ['Workflow 1']},
        {'id': 1701805543444, 'name': 'Cookie Batch', 'workflow': ['Workflow 2']}, 
        {'id': 1701805546966, 'name': 'Cookie Batch', 'workflow': ['Workflow 2']},
    ],
    'equipment': [
        {'name': 'Mixer', 'category': 'Mixing', 'task': 'Mixing', 'duration': '20'},
        {'name': 'Oven', 'category': 'Heating', 'task': 'Heating', 'duration': '40'},
        {'name': 'Cooling Rack', 'category': 'Cooling', 'task': 'Cooling', 'duration': '20'},
    ],
    'constraints': [
        {'description': "The mixer can't run when the oven is in use"}
    ],
    'workflows': [
        {'name': 'Workflow 1', 'equipment': ['Mixer', 'Oven', 'Cooling Rack']}, 
        {'name': 'Workflow 2', 'equipment': ['Mixer', 'Oven']}
    ],
    'schedule': {'startDate': '2023-12-05', 'startTime': '15:45'},
    'message': """You are a scheduling agent for the batches and associated workflows that I give you.
     
    I have multiple batch ids which have an associated workflow outlined in the provided JSON data, involving the use of shared equipment in a 
    factory setting. Using the start time provided in the JSON block, create an optimized schedule that maximizes equipment usage from the 
    starting time and runs the processes as fast as possible, NEVER letting the equipment be idle unless a constraint requires it or 
    there are no more batches to run. If a piece of equipment becomes available and there's another batch to run, START THE BATCH. 
    We are looking to maximize concurrency and WE WANT PARALLEL BATCH EXECUTION. As soon as one part of a workflow finishes with a 
    piece of equipment, it's available for the next batch with that piece of equipment in its workflow. THIS IS OPTIMIZED IF the 
    equipment is continuously running and the schedule isn't necessarily completing one entire workflow before starting another. Base 
    the start and end times for each part of the workflow on the equipment use duration provided. The duration given is in minutes.

    IMPORTANT THAT When you calculate this keep track of whether each piece of equipment is free or being used and as soon as it's free, look
    to schedule another batch with that piece of equipment as soon as possible. MAXIMIZE EQUIPMENT USAGE 

    PLEASE RETURN the name of the activity as "Batch ID (Workflow Equipment)" 

    IT IS NOT NECESSARY FOR A BATCH TO BE COMPLETE BEFORE ANOTHER BATCH STARTS 
    PLEASE PAY ATTENTION TO THE WORKFLOWS. IF A BATCH WORKFLOW DOESN'T HAVE A PIECE OF EQUIPMENT IN IT THEN THERE SHOULDN'T BE 
    AN ACTIVITY ON THAT MACHINE WITH THAT BATCH ID. A piece of equipment can only be used by one batch at a time. 
    """
}

manufacturing_demo = {
    'activities': [],
    'equipment': [
        {'name': '1 Liter Bioreactor', 'category': 'Small Bioreactor', 'task': 'Bioreactor', 'duration': '60'},
        {'name': '5 Liter Bioreactor', 'category': 'Small Bioreactor', 'task': 'Bioreactor', 'duration': '40'},
        {'name': '100 Liter Bioreactor', 'category': 'Small Bioreactor', 'task': 'Bioreactor', 'duration': '20'},
        {'name': '1000 Liter Bioreactor', 'category': 'Large Bioreactor', 'task': 'Bioreactor', 'duration': '40'},
        {'name': '5000 Liter Bioreactor', 'category': 'Large Bioreactor', 'task': 'Bioreactor', 'duration': '20'},
    ],
    'constraints': [
        {'description': "The 1 Liter Bioreactor can't be running at the same time as the 5 Liter Bioreactor"}
    ],
    'workflows': [
        {'name': 'Workflow 1', 'equipment': ['1 Liter Bioreactor', '5 Liter Bioreactor', '100 Liter Bioreactor', '1000 Liter Bioreactor', '5000 Liter Bioreactor']}, 
        {'name': 'Workflow 2', 'equipment': ['1 Liter Bioreactor', '5 Liter Bioreactor', '100 Liter Bioreactor']},
        {'name': 'Workflow 3', 'equipment': ['100 Liter Bioreactor', '1000 Liter Bioreactor', '5000 Liter Bioreactor']},
        {'name': 'Workflow 4', 'equipment': ['1 Liter Bioreactor', '5 Liter Bioreactor', '1000 Liter Bioreactor']},
    ],
    'schedule': {'startDate': '2023-12-05', 'startTime': '15:45'},
    'message': """You are a scheduling agent for the batches and associated workflows that I give you.
     
    I have multiple batch ids which have an associated workflow outlined in the provided JSON data, involving the use of shared equipment in a 
    factory setting. Using the start time provided in the JSON block, create an optimized schedule that maximizes equipment usage from the 
    starting time and runs the processes as fast as possible, NEVER letting the equipment be idle unless a constraint requires it or 
    there are no more batches to run. If a piece of equipment becomes available and there's another batch to run, START THE BATCH. 
    We are looking to maximize concurrency and WE WANT PARALLEL BATCH EXECUTION. As soon as one part of a workflow finishes with a 
    piece of equipment, it's available for the next batch with that piece of equipment in its workflow. THIS IS OPTIMIZED IF the 
    equipment is continuously running and the schedule isn't necessarily completing one entire workflow before starting another. Base 
    the start and end times for each part of the workflow on the equipment use duration provided. The duration given is in minutes.

    IMPORTANT THAT When you calculate this keep track of whether each piece of equipment is free or being used and as soon as it's free, look
    to schedule another batch with that piece of equipment as soon as possible. MAXIMIZE EQUIPMENT USAGE 

    PLEASE RETURN the name of the activity as "Batch ID (Workflow Equipment)" 

    IT IS NOT NECESSARY FOR A BATCH TO BE COMPLETE BEFORE ANOTHER BATCH STARTS 
    PLEASE PAY ATTENTION TO THE WORKFLOWS. IF A BATCH WORKFLOW DOESN'T HAVE A PIECE OF EQUIPMENT IN IT THEN THERE SHOULDN'T BE 
    AN ACTIVITY ON THAT MACHINE WITH THAT BATCH ID. A piece of equipment can only be used by one batch at a time. 
    """
}

optimized_schedule = {}

# Load OpenAI API key
@app.route('/')
def index():
    return render_template('home.html')

# Equipment page route
@app.route('/equipment')
def equipment_page():
    return render_template('equipment.html')

# Workflows page route
@app.route('/workflows')
def workflows_page():
    return render_template('workflows.html')

# Activities page route
@app.route('/activities')
def activities_page():
    return render_template('activities.html')

# Constraints page route
@app.route('/constraints')
def constraints_page():
    start_date = data['schedule']['startDate'] if data['schedule']['startDate'] else ''
    start_time = data['schedule']['startTime'] if data['schedule']['startTime'] else ''
    return render_template('constraints.html', message=data['message'], start_date=start_date, start_time=start_time)

# Review and submit page route
@app.route('/review-submit')
def review_page():
    # Fetch data to be displayed on the review page
    activities = data['activities']
    constraints = data['constraints']
    start_date = data['schedule']['startDate'] if data['schedule']['startDate'] else ''
    start_time = data['schedule']['startTime'] if data['schedule']['startTime'] else ''
    prompt_message = data['message']
    return render_template('review_submit.html', 
                           activities=activities, 
                           constraints=constraints, 
                           start_date=start_date,
                           start_time=start_time,
                           message=prompt_message)

# Route to add items (activities, equipment, etc.)
@app.route('/add/<category>', methods=['POST'])
def add_item(category):
    item = request.json
    data[category].append(item)
    return jsonify(data=data)

# Route to submit and process data
@app.route('/submit', methods=['POST'])
def submit_data():
    message = data['message']

    schedule_data = {m: n for m,n in data.items() if m != 'message'}

    schedule_data['activities'] = reformat_activities(schedule_data)

    print(schedule_data)

    message = message + str(schedule_data)

    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "user", "content": message}
        ],
        functions=[
            {
            "name": "optimizeWorkflow",
            "parameters": {
                "type": "object",
                "properties": {
                "activities": {
                    "type": "array",
                    "items": {
                    "type": "object",
                    "properties": {
                        "activity_id": {"type": "string"},
                        "activityName": {"type": "string"},
                        "startTime": {"type": "string", "format": "date-time"},
                        "endTime": {"type": "string", "format": "date-time"},
                        "equipment": {"type": "string"}
                    },
                    "required": ["activity_id", "activityName", "startTime", "endTime", "equipment"]
                    }
                }
                },
                "required": ["activities"]
            }
            }
        ]
    )

    print(response.choices[0].message)
    function_call = response.choices[0].message.get("function_call", {})
    arguments_str = function_call.get("arguments", "{}")

    try:
        # Parse the JSON string in 'arguments' to a Python dictionary
        optimized_schedule = json.loads(arguments_str)
        data['optimized_schedule'] = optimized_schedule['activities']  # Store in 'data' dictionary
    except:
        submit_data()

    return jsonify({'success': True})


def reformat_activities(data):
    # This function reformats activities by appending the equipment to the activity name
    reformatted_activities = []

    for activity in data['activities']:
        activity_workflow = ''
        for workflow in data['workflows']:
            if workflow['name'] == activity['workflow'][0]:
                activity_workflow = workflow
        for equipment in activity_workflow['equipment']:
            reformatted_activities.append({'name': str(activity['id']) + '/' + equipment, 'equipment': equipment})

    return reformatted_activities

@app.route('/get-data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/gantt-chart')
def gantt_chart():
    if 'optimized_schedule' in data and data['optimized_schedule']:
        # Create DataFrame from the optimized_schedule data
        df = pd.DataFrame(data['optimized_schedule'])

        # Convert startTime and endTime to datetime objects
        df['startTime'] = pd.to_datetime(df['startTime'])
        df['endTime'] = pd.to_datetime(df['endTime'])

        # Create Plotly figure
        fig = px.timeline(df, x_start="startTime", x_end="endTime", y="activityName", title="Optimized Workflow Schedule")
        fig.update_yaxes(autorange="reversed")  # for top-to-bottom layout
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('gantt_chart.html', graphJSON=graphJSON)
    else:
        # Return a different page or a message if optimized_schedule is empty or not in data
        return render_template('error.html', message="No data available for Gantt chart.")
    
@app.route('/update-message', methods=['POST'])
def update_message():
    updated_message = request.json.get('message')
    data['message'] = updated_message  # Update the message in the data dictionary
    return jsonify({'success': True})

@app.route('/delete/<category>', methods=['POST'])
def delete_item(category):
    print(data)
    if(category == 'activities'):
        item_to_delete = int(request.json['name'])
        data[category] = [item for item in data[category] if item['id'] != item_to_delete]
    elif(category == 'constraints'):
        item_to_delete = request.json['name']
        data[category] = [item for item in data[category] if item['description'] != item_to_delete]
    else:
        item_to_delete = request.json['name']
        data[category] = [item for item in data[category] if item['name'] != item_to_delete]
        
    return jsonify(data=data)

# Route to update the start time
@app.route('/update-start-time', methods=['POST'])
def update_start_time():
    updated_start_time = request.json
    data['schedule']['startDate'] = updated_start_time['startDate']
    data['schedule']['startTime'] = updated_start_time['startTime']
    # Optionally, extract and store start time separately if needed
    return jsonify({'success': True})

# Route to set demo data
@app.route('/set-demo-data', methods=['POST'])
def set_demo_data():
    global data
    data = demo_data.copy()  # Copy the demo data into the main data variable
    return jsonify({'success': True, 'message': 'Demo data set successfully.'})

@app.route('/set-manufacturing-demo-data', methods=['POST'])
def set_manufacturing_demo_data():
    global data
    data = manufacturing_demo.copy()  # Copy the demo data into the main data variable
    return jsonify({'success': True, 'message': 'Demo data set successfully.'})

# Route to upload CSV and parse it
@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    global data  # Ensure you're modifying the global data variable
    file = request.files['csvfile']
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    next(csv_input, None)  # Skip the header row

    for row in csv_input:
        # Assuming the CSV format is: BatchName, Workflow
        batch_name, workflow = row
        # Generate an ID for the activity (can be replaced with a better method)
        activity_id = int(time.time() * 1000)
        data['activities'].append({'id': activity_id, 'name': batch_name, 'workflow': [workflow]})

    return jsonify(data=data)

@app.route('/get-equipment', methods=['GET'])
def get_equipment():
    return jsonify(data['equipment'])

@app.route('/create-workflow', methods=['POST'])
def create_workflow():
    workflow = request.json
    data['workflows'].append(workflow)
    return jsonify(success=True, message="Workflow added successfully.")

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=False)
