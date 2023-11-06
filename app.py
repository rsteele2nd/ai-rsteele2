from flask import Flask, jsonify, render_template, request
import os
import openai

app = Flask(__name__)

# Load OpenAI API key from environment variable
openai.api_key = ""

# In-memory data storage
data = {
    "activities": [],
    "equipment": [],
    "constraints": [],
    "schedule": {
        "startDate": None,
        "endDate": None
    }
}

@app.route('/')
def index():
    return render_template('index.html')

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

    message = "Using the provided JSON data which outlines a set of activities, the associated equipment with their durations, and a constraint for a factory scenario,generate an optimized schedule for these activities. The schedule should maximize the use of time and equipment while respecting the constraints."
    message = message + str(schedule_data)
    messae = message + """Please create an optimized batch schedule that adheres to the workflow sequence, 
    equipment usage duration, and the constraint that the mixer cannot be used simultaneously with the cooling rack. 
    The schedule should ensure that all activities are completed within the given time frame and that no equipment is used 
    by more than one activity at the same time. 
    The output should be in the following JSON format, detailing the start and end times for each task:
    {
        "optimizedSchedule": [
            {
            "activityId": "integer",
            "activityName": "string",
            "tasks": [
                {
                "taskName": "string",
                "startTime": "YYYY-MM-DD HH:MM",
                "endTime": "YYYY-MM-DD HH:MM"
                },
                {
                // More tasks
                }
            ]
            },
            // More activities
        ]
        "unassignableTasks": [
            {
                // same format as optimized schedule 
            }
        ]
        } 

    Ensure that the startTime and endTime for each task are computed based on the duration of the equipment use which is in minutes and that the tasks within an 
    activity follow the workflow sequence provided. Only return the json block of optimized data that you have. Return no text about your process or anything 
    but the json block in the specific format. 
    """


    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": message},
        ],
        functions=
        [
            {
                "name": "function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "optimizedSchedule": {
                            "type": "object",
                            "description": "Optimized schedule",
                            "properties": {
                                "activity_id": {"type": "string"},
                                "activityName": {"type": "string"},
                                "workflow": {
                                    "type": "object",
                                    "properties": {
                                        "equipment": {"type": "string"},
                                        "startTime": {"type": "string"},
                                        "endTime": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    )

    print(response)
    return jsonify(success=True)

@app.route('/get-data', methods=['GET'])
def get_data():
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
