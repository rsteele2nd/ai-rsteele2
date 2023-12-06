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
                if (category === 'workflows') {
                    fetchEquipment(); // Refetch equipment to reset the sortable list
                }
            },
            error: function(xhr, status, error) {
                console.error("Error adding " + category + ": " + error);
            }
        });
    }

    function deleteItem(category, name) {
        $.ajax({
            url: '/delete/' + category,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ name: name }),
            dataType: 'json',
            success: function(response) {
                // Remove the corresponding row based on the category
                if (category === 'equipment') {
                    $('#equipment-row-' + name).remove();
                } else if (category === 'activities') {
                    $('#activity-row-' + name).remove();
                } else if (category === 'workflows') {
                    $('#workflow-row-' + name).remove();
                } else if (category === 'constraints') {
                    $('#constraint-row-' + name).remove();
                }
    
                updateTables(response.data); // Update other tables if needed
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
            activitiesTable.append('<tr id="activity-row-' + activity.id + '">' +
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
            equipmentTable.append('<tr id="equipment-row-' + item.name + '">' +
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
            constraintsTable.append('<tr id="constraint-row-' + constraint.description + '">' +
                '<td>' + constraint.description + '</td>' +
                '<td><button onclick="deleteItem(\'constraints\', \'' + constraint.description + '\')">Delete</button></td>' +
            '</tr>');
        });

        // Update Workflows Table
        var workflowsTable = $('#workflows-table tbody');
        workflowsTable.empty();
        $.each(data.workflows, function(index, workflow) {
            workflowsTable.append('<tr id="workflow-row-' + workflow.name + '">' +
                '<td>' + workflow.name + '</td>' +
                '<td>' + workflow.equipment.join(", ") + '</td>' +
                '<td><button onclick="deleteItem(\'workflows\', \'' + workflow.name + '\')">Delete</button></td>' +
            '</tr>');
        });
    }

    // Fetch Equipment and Update Multi-select
    function fetchEquipment() {
        $.ajax({
            url: '/get-equipment',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                var equipmentList = $('#sortable-equipment');
                equipmentList.empty(); // Clear existing items
    
                $.each(response, function(index, equipment) {
                    var listItem = $('<li class="list-group-item d-flex align-items-center" data-equipment-name="' + equipment.name + '"></li>');
                    listItem.append('<input type="checkbox" class="me-2" checked>');
                    listItem.append(equipment.name);
                    equipmentList.append(listItem);
                });
    
                // Make the list sortable
                equipmentList.sortable();
                equipmentList.disableSelection();
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

    function createWorkflow(name, equipment) {
        $.ajax({
            url: '/create-workflow',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ name: name, equipment: equipment }),
            dataType: 'json',
            success: function(response) {
                alert('Workflow created successfully');
                // Optionally, update the UI with the new workflow
            },
            error: function(xhr, status, error) {
                console.error("Error creating workflow: " + error);
            }
        });
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
        var startDate = $('#schedule-start-date').val().trim();
        var startTime = $('#schedule-start-time').val().trim();
    
        // Send the updated start time to the server
        $.ajax({
            url: '/update-start-time',  // You need to create this route in Flask
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ startDate: startDate, startTime: startTime }),
            dataType: 'json',
            success: function(response) {
                alert('Start time updated successfully!');
            },
            error: function(xhr, status, error) {
                console.error("Error updating start time: " + error);
            }
        });
    });

    // Handler for adding a workflow
    $('#workflow-form').on('submit', function(e) {
        e.preventDefault();
    
        var workflowName = $('#workflow-name').val().trim();
        var selectedEquipment = [];
    
        $('#sortable-equipment').children().each(function() {
            var isChecked = $(this).find('input[type="checkbox"]').is(':checked');
            if (isChecked) {
                var equipmentName = $(this).data('equipment-name');
                selectedEquipment.push(equipmentName);
            }
        });
    
        var workflow = {
            name: workflowName,
            equipment: selectedEquipment
        };
    
        addItem('workflows', workflow);
        $('#workflow-name').val('');
        $('#sortable-equipment').empty();
    });
    
    $('#submit-data-button').on('click', function() {
        // Make the AJAX POST request to the /submit route
        $.ajax({
            url: '/submit',
            type: 'POST',
            contentType: 'application/json',
            data: null,
            dataType: 'json',
            success: function(response) {
                alert('Data submitted successfully!');
                // Handle the response here
            },
            error: function(xhr, status, error) {
                alert('Error submitting data: ' + error);
            }
        });
    });

    $('#prompt-form').on('submit', function(e) {
        e.preventDefault();
        var updatedMessage = $('#prompt-text').val().trim();
    
        // Send the updated message to the server
        $.ajax({
            url: '/update-message',  // You'll need to create this route in Flask
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: updatedMessage }),
            dataType: 'json',
            success: function(response) {
                // Handle response
            },
            error: function(xhr, status, error) {
                console.error("Error updating message: " + error);
            }
        });
    });

    $('#csv-upload-form').on('submit', function(e) {
        e.preventDefault();
        var fileInput = $('#csv-file')[0];
        var formData = new FormData();
        formData.append('csvfile', fileInput.files[0]);
    
        $.ajax({
            url: '/upload-csv',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Update activities table with new data
                updateTables(response.data);
            },
            error: function(xhr, status, error) {
                console.error("Error uploading CSV: " + error);
            }
        });
    });    

    // Expose deleteItem to global scope to be callable from onclick
    window.deleteItem = deleteItem;
});
