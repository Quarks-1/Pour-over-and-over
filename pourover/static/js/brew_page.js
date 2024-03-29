"use strict"

let socket = null


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
        if (Array.isArray(response)) {
            updateParams(response)
        } else {
            displayResponse(response)
        }
    }
}

function displayError(message) {
    let errorElement = document.getElementById("error")
    alert(message);
}

function displayMessage(message) {
    let errorElement = document.getElementById("message")
    alert(message)
}

function displayResponse(response) {
    if ("error" in response) {
        displayError(response.error)
    } else if ("message" in response) {
        displayMessage(response.message)
    } else {
        displayMessage("Unknown response")
    }
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
    let pauseBrewButton = document.getElementById("id_pause_brew_button")
    pauseBrewButton.disabled = false
    socket.send(JSON.stringify({"command": "startBrew"}))
}

function pauseBrew() {
    let pauseBrewButton = document.getElementById("id_pause_brew_button")
    pauseBrewButton.disabled = true
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = false
    socket.send(JSON.stringify({"command": "pauseBrew"}))
}

function stopBrew() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = true
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = false
    let pauseBrewButton = document.getElementById("id_pause_brew_button")
    pauseBrewButton.disabled = true
    socket.send(JSON.stringify({"command": "stopBrew"}))
}

function restartBrew() {
    let stopBrewButton = document.getElementById("id_stop_brew_button")
    stopBrewButton.disabled = false
    let brewButton = document.getElementById("id_start_brew_button")
    brewButton.disabled = true
    let pauseBrewButton = document.getElementById("id_pause_brew_button")
    pauseBrewButton.disabled = false
    socket.send(JSON.stringify({"command": "restartBrew"}))
}