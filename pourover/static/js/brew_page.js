"use strict"

let socket = null
let startTime = Date.now()
let started = false
let buttonIDs = ["id_start_brew_button", "id_stop_brew_button", "id_restart_brew_button", "id_tare_button", "id_bypass_heater", "id_start_heater"]

function connectToServer() {
    // Use wss: protocol if site using https:, otherwise use ws: protocol
    let wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"

    // Create a new WebSocket.
    let url = `${wsProtocol}//${window.location.host}/pourover/data`
    socket = new WebSocket(url)

    // Handle any errors that occur.
    socket.onerror = function(error) {
        console.log('error!')
        console.log(error)
    }

    // Show a connected message when the WebSocket is opened.
    socket.onopen = function(event) {
        console.log('connected!')
        console.log(`Profile ID: ${document.getElementById("id_profile_id").innerHTML}`)
        socket.send(JSON.stringify({"command": "profileSelect", "profile": document.getElementById("id_profile_id").innerHTML}))
    }

    // Show a disconnected message when the WebSocket is closed.
    socket.onclose = function(event) {
        console.log('disconnected!')
    }

    // Handle messages received from the server.
    socket.onmessage = function(event) {
        let response = JSON.parse(event.data)
        if (response['type'] == 'message') {
            if (response['message'] == 'start data feed') {
            setInterval(() => {
                socket.send(JSON.stringify({"command": "updateData"}));
            }, 500);
            }
            else if (response['message'].includes('curr step')) {
                let step = response['message'].split(':')[1]
                highlightStep(step)
            }
            else if (response['message'].includes('disable heater button')) {
                disableButton("id_start_heater")
            }
            else if (response['message'].includes('disable bypass button')) {
                disableButton("id_bypass_heater")
            }
            else if (response['message'].includes('enable buttons')) {
                disableButton("id_bypass_heater")
            }
            else if (response['message'].includes('enable all buttons')) {
                for (let i = 0; i < buttonIDs.length; i++) {
                    enableButton(buttonIDs[i])
                }
            }
            else {
                displayMessage(response['message'])
                if (response['message'].includes("not connected")) {
                    disableButtons()
                }
            }
        }

        else if (response['type'] == 'data') {
            let weight = document.getElementById("id_brew_weight")
            let temp = document.getElementById("id_brew_temp")
            let time = document.getElementById("id_brew_time")
            weight.innerHTML = response['data']['weight']
            temp.innerHTML = response['data']['temp']
            if (started == true){
                time.innerHTML = getCurrentTimeDifference()
            }
            else {
                time.innerHTML = "00:00"
            }
        }

        else {
            displayMessage(response)
                
        }
    }
}

function highlightStep(step) {
    let steps = document.getElementById("id_step_table").getElementsByTagName("tr");
    for (let i = 0; i < steps.length; i++) {
        if (i == step) {
            steps[i].style.backgroundColor = "lightgreen"
        }
        else {
            steps[i].style.backgroundColor = "transparent";
        }
    }
}

function displayMessage(message) {
    let errorElement = document.getElementById("id_brew_status")
    errorElement.innerHTML = message
}

function updateParams(data) {
    // placeholder code to display the data
    // Update to page values later
    let params = document.getElementById("params")
    params.innerHTML = ""
    for (let i = 0; i < data.length; i++) {
        let param = data[i]
        let paramElement = document.createElement("li")
        paramElement.innerHTML = param
        params.appendChild(paramElement)
    }
}


function enableButton(id) {
    let button = document.getElementById(id)
    button.disabled = false
}

function disableButton(id) {
    let button = document.getElementById(id)
    button.disabled = true
}

function startBrew() {
    enableButton("id_stop_brew_button")
    disableButton("id_start_brew_button")
    startTime = Date.now() // Reset the start time
    started = true
    socket.send(JSON.stringify({"command": "startBrew"}))
}

function stopBrew() {
    disableButton("id_stop_brew_button")
    enableButton("id_start_brew_button")
    socket.send(JSON.stringify({"command": "stopBrew"}))
}

function restartBrew() {
    enableButton("id_stop_brew_button")
    disableButton("id_start_brew_button")
    startTime = Date.now() // Reset the start time
    socket.send(JSON.stringify({"command": "restartBrew"}))
}

function disableButtons() {
    disableButton("id_stop_brew_button")
    disableButton("id_start_brew_button")
    disableButton("id_restart_brew_button")
}

function getCurrentTimeDifference() {
    let now = new Date(); 
    let difference = now - startTime; 
    let minutes = Math.floor(difference / 60000); 
    let seconds = Math.floor((difference % 60000) / 1000);
    minutes = minutes < 10 ? '0' + minutes : minutes;
    seconds = seconds < 10 ? '0' + seconds : seconds;
    return minutes + ':' + seconds;
}

function tareScale() {
    console.log('taring')
    socket.send(JSON.stringify({"command": "tareScale"}))
}

function bypassTemp() {
    socket.send(JSON.stringify({"command": "bypassTemp"}))
}

function startHeater() {
    socket.send(JSON.stringify({"command": "startHeater"}))
}