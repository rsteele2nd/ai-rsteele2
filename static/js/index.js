$(document).ready(function() {
    function addItem(category, item) {
        $.ajax({
            url: '/add/' + category,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(item),
            dataType: 'json',
            success: function(response) {
                updateTables(response.data);
                fetchWorkflows();
            }
        });
    }

    function deleteItem(category, idOrName) {
        $.ajax({
            url: '/delete/' + category,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ id: idOrName }),
            dataType: 'json',
            success: function(response) {
                updateTables(response.data);
            }
        });
    }

    function fetchDataAndUpdateTables() {
        $.ajax({
            url: '/get-data',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                updateTables(response);
                fetchEquipment();
                fetchWorkflows();
            },
            error: function(xhr, status, error) {
                console.error("Error fetching data: " + error);
            }
        });
    }

    // Call this function when the page loads
    fetchDataAndUpdateTables();

    function updateTables(data) {
        // Update Equipment Select Options
        var workflowSelect = $('#activity-workflow');
        workflowSelect.empty(); // Clear the select first
        $.each(data.equipment, function(index, equipment) {
            workflowSelect.append($('<option>', {
                value: equipment.name,
                text : equipment.name
            }));
        });

        // Update Activities Table
        var activitiesTable = $('#activities-table tbody');
        activitiesTable.empty();
        $.each(data.activities, function(index, activity) {
            activitiesTable.append('<tr>' +
                '<td>' + activity.id + '</td>' +
                '<td>' + activity.name + '</td>' +
                '<td>' + activity.workflow.join(", ") + '</td>' +
                '<td><button onclick="deleteItem(\'activities\', \'' + activity.id + '\')">Delete</button></td>' +
            '</tr>');
        });

        // Update Equipment Table
        var equipmentTable = $('#equipment-table tbody');
        equipmentTable.empty(); // Clear the table first
        $.each(data.equipment, function(index, item) {
            equipmentTable.append('<tr>' +
                '<td>' + item.name + '</td>' +
                '<td>' + item.category + '</td>' +
                '<td>' + item.task + '</td>' +
                '<td>' + item.duration + '</td>' +
                '<td><button onclick="deleteItem(\'equipment\', \'' + item.name + '\')">Delete</button></td>' +
            '</tr>');
        });

        // Update Constraints Table
        var constraintsTable = $('#constraints-table tbody');
        constraintsTable.empty(); // Clear the table first
        $.each(data.constraints, function(index, constraint) {
            constraintsTable.append('<tr>' +
                '<td>' + constraint.description + '</td>' +
                '<td><button onclick="deleteItem(\'constraints\', \'' + constraint.description + '\')">Delete</button></td>' +
            '</tr>');
        });

        // Update Workflows Table
        var workflowsTable = $('#workflows-table tbody');
        workflowsTable.empty();
        $.each(data.workflows, function(index, workflow) {
            workflowsTable.append('<tr>' +
                '<td>' + workflow.name + '</td>' +
                '<td>' + workflow.equipment.join(", ") + '</td>' +
                '<td><button onclick="deleteItem(\'workflows\', \'' + workflow.name + '\')">Delete</button></td>' +
            '</tr>');
        });
    }

    // Fetch Equipment and Update Multi-select
    function fetchEquipment() {
        $.ajax({
            url: '/get-data',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                var equipmentSelect = $('#equipment-select');
                equipmentSelect.empty();
                $.each(response.equipment, function(index, equipment) {
                    equipmentSelect.append($('<option>', {
                        value: equipment.name,
                        text: equipment.name
                    }));
                });
            },
            error: function(xhr, status, error) {
                console.error("Error fetching equipment: " + error);
            }
        });
    }

    function fetchWorkflows() {
        $.ajax({
            url: '/get-data',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                var workflowSelect = $('#activity-workflow');
                workflowSelect.empty();
                $.each(response.workflows, function(index, workflow) {
                    workflowSelect.append($('<option>', {
                        value: workflow.name,
                        text: workflow.name
                    }));
                });
            },
            error: function(xhr, status, error) {
                console.error("Error fetching workflows: " + error);
            }
        });
    }

    function redirectToGanttChart() {
        window.location.href = '/gantt-chart'; // URL of your Gantt chart page
    }

    // Handler for adding an activity
    $('#activity-form').on('submit', function(e) {
        e.preventDefault();
        var selectedWorkflow = $('#activity-workflow').val() || [];
        var activity = {
            id: Date.now(), // Using a timestamp as a simple unique ID
            name: $('#activity-name').val().trim(),
            workflow: selectedWorkflow
        };
        addItem('activities', activity);
        $('#activity-name').val('');
        $('#activity-workflow').val([]); // Clear selected options
    });

    $('#equipment-form').on('submit', function(e) {
        e.preventDefault();
        var equipment = {
            name: $('#equipment-name').val().trim(),
            category: $('#equipment-category').val().trim(),
            task: $('#equipment-task').val().trim(),
            duration: $('#equipment-duration').val().trim()
        };
        addItem('equipment', equipment);
        $('#equipment-name').val('');
        $('#equipment-category').val('');
        $('#equipment-task').val('');
        $('#equipment-duration').val('');
    });

    $('#constraint-form').on('submit', function(e) {
        e.preventDefault();
        var constraint = {
            description: $('#constraint-text').val().trim()
        };
        addItem('constraints', constraint);
        $('#constraint-text').val('');
    });

    $('#config-form').on('submit', function(e) {
        e.preventDefault();

        // Inform the user that the configuration has been saved
        alert('Configuration saved!');
    });

    // Handler for adding a workflow
    $('#workflow-form').on('submit', function(e) {
        e.preventDefault();
        var selectedEquipment = $('#equipment-select').val() || [];
        var workflow = {
            name: $('#workflow-name').val().trim(),
            equipment: selectedEquipment
        };
        addItem('workflows', workflow);
        $('#workflow-name').val('');
        $('#equipment-select').val([]); // Clear selected options
    });


    $('#submit-data').on('click', function() {
        // Make an AJAX GET request to fetch the data first
        $.ajax({
            url: '/get-data',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                // 'response' now holds the data fetched from the server
                const scheduleData = {
                    startDate: $('#schedule-start-date').val().trim() + ' ' + $('#schedule-start-time').val().trim(),
                    endDate: $('#schedule-end-date').val().trim() + ' ' + $('#schedule-end-time').val().trim(),
                    activities: response.activities,  // Use the fetched data
                    equipment: response.equipment,    // Use the fetched data
                    constraints: response.constraints, // Use the fetched data
                    workflow: response.workflow
                };

                // Now send the scheduleData to the server
                $.ajax({
                    url: '/submit',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(scheduleData),
                    dataType: 'json',
                    success: function(submitResponse) {
                        if (submitResponse.success) {
                            $('#json-output').text(JSON.stringify(scheduleData, null, 2));
                            redirectToGanttChart(); // Call the function to redirect
                        } else {
                            alert('Error: Submission failed.');
                        }
                    },
                    error: function(xhr, status, submitError) {
                        alert('An error occurred: ' + submitError);
                    }
                });
            },
            error: function(xhr, status, fetchError) {
                alert('An error occurred fetching data: ' + fetchError);
            }
        });
    });

    // Expose deleteItem to global scope to be callable from onclick
    window.deleteItem = deleteItem;
});
