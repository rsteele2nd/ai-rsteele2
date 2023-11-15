from flask import Flask, jsonify, render_template, request, redirect, url_for
import os
import openai
import plotly.express as px
import pandas as pd
import json
import plotly

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
        "endDate": None
    }
}

optimized_schedule = {}

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/equipment')
def equipment_page():
    return render_template('equipment.html')

@app.route('/workflows')
def workflows_page():
    return render_template('workflows.html')

@app.route('/activities')
def activities_page():
    return render_template('activities.html')

@app.route('/constraints')
def constraints_page():
    return render_template('constraints.html')

@app.route('/add/<category>', methods=['POST'])
def add_item(category):
    item = request.json
    data[category].append(item)
    return jsonify(data=data)

@app.route('/delete/<category>', methods=['POST'])
def delete_item(category):
    item_to_delete = request.json['name']
    data[category] = [item for item in data[category] if item['name'] != item_to_delete]
    return jsonify(data=data)

@app.route('/submit', methods=['POST'])
def submit_data():
    schedule_data = request.json  # Collect data from the request
    # Here you would process the schedule_data as needed and potentially call OpenAI's API
    # But for this example, we're just printing it to the console
    print(schedule_data)

    message = """You are a scheduling agent for the batches and associated workflows that I give you.
     
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
    AN ACTIVITY ON THAT MACHINE WITH THAT BATCH ID.
    """
    message = message + str(schedule_data)

    response = openai.ChatCompletion.create(
        model="gpt-4",
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

    # Parse the JSON string in 'arguments' to a Python dictionary
    optimized_schedule = json.loads(arguments_str)
    data['optimized_schedule'] = optimized_schedule['activities']  # Store in 'data' dictionary

    return jsonify({'success': True})

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

if __name__ == '__main__':
    app.run(debug=True)
