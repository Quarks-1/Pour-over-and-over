const steps = [];
const prettySteps = [];

function addStep() {
    let input = document.getElementsByName('stepVals');
    let step = `${input[0].value}/${input[1].value}/${input[2].value}/${input[3].value}`
    let prettyStep = [input[0].value, input[1].value, input[2].value, input[3].value];
    steps.push(step);
    prettySteps.push(prettyStep);
    renderSteps();
};

// Passes JS data into Django form input fields
function submitSteps() {
    // Add pre wet
    let pre_wet = document.getElementById('id_pre_wet').checked;
    if (pre_wet == true) {
        steps.unshift(('pre_wet/0/0/0'));
        prettySteps.unshift(['pre_wet', 0, 0, 0]);
    }
    // Add steps to form
    document.getElementById('id_steps').value = JSON.stringify(steps);
    // Calculate total water weight
    let total_water = 0;
    for (let i = 0; i < steps.length; i++) {
        if (prettySteps[i][0] == 'pre_wet') {
            continue;
        }
        total_water += parseInt(prettySteps[i][1]);
    }
    document.getElementById('id_total_water_weight').value = total_water;
};

function renderSteps() {
    const currStepsElement = document.getElementById('currSteps');
    // Clear existing steps
    currStepsElement.innerHTML = '';
    
    for (let i = 0; i < steps.length; i++) {
        // Create a div for each step and append it
        const stepDiv = document.createElement('div');
        stepDiv.innerHTML = (i + 1) + ': (' + prettySteps[i] + ')';
        currStepsElement.appendChild(stepDiv);
    }
}


function removeStep() {
    step_number = document.getElementById('removeStep_input').value;
    if (step_number < 1 || step_number > steps.length) {
        alert('Invalid step number');
        return;
    }
    steps.pop(step_number-1);
    prettySteps.pop(step_number-1);
    renderSteps();
};
