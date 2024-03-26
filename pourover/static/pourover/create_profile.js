const steps = [];

function removeStep() {
    step_number = document.getElementById('removeStep').value;
    steps.pop(step_number-1);
    document.getElementById('currSteps').innerHTML = '';
    for (let i = 0; i < steps.length; i++) {
        document.getElementById('currSteps').innerHTML += (i+1) + ': (' + steps[i] + ')' + "<br>";
    }
    document.getElementById('currSteps').innerHTML = document.getElementById('currSteps').innerHTML.slice(0, -1);
}

function addToSteps() {
    let input = document.getElementsByName('stepVals');
    let step = [input[0].value, input[1].value, input[2].value, input[3].value];
    steps.push(step);
    document.getElementById('currSteps').innerHTML = '';
    for (let i = 0; i < steps.length; i++) {
        document.getElementById('currSteps').innerHTML += (i+1) + ': (' + steps[i] + ')' + "<br>";
    }
    document.getElementById('currSteps').innerHTML = document.getElementById('currSteps').innerHTML.slice(0, -1);
}

document.getElementById('removeStep_input').addEventListener('keydown', function(k){
    if(k.keyCode == 13) return false;
});