"use strict"

let socket = null
let startTime = Date.now()
let started = false


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


function startBrew() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = false
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = true
    startTime = Date.now() // Reset the start time
    socket.send(JSON.stringify({"command": "startBrew"}))
}

function stopBrew() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = true
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = false
    socket.send(JSON.stringify({"command": "stopBrew"}))
}

function restartBrew() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = false
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = true
    startTime = Date.now() // Reset the start time
    socket.send(JSON.stringify({"command": "restartBrew"}))
}

function disableButtons() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = true
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = true
    let restartBrewButton = document.getElementById("id_restart_brew_button")
    restartBrewButton.disabled = true
}

function getCurrentTimeDifference() {
    let now = new Date(); // Current time
    let difference = now - startTime; // Difference in milliseconds

    // Convert milliseconds into minutes and seconds
    let minutes = Math.floor(difference / 60000); // 60,000 milliseconds in a minute
    let seconds = Math.floor((difference % 60000) / 1000); // Remaining milliseconds converted to seconds

    // Formatting minutes and seconds to ensure two digits
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