// 1D36DE6AFA40447680E9CAA3C214C671
function connect() {

}

var domReady = function(callback) {
    document.readyState === "interactive" || document.readyState === "complete" ? callback() : document.addEventListener("DOMContentLoaded", callback);		
};

domReady(function() {
    getJobInfo();
    getPrinterInfo();
});

function getJobInfo(){
    var xmlhttp = new XMLHttpRequest();


    xmlhttp.onload = function() {

        var reads = JSON.parse(this.responseText);
        document.getElementById("lblfileName").innerText = reads.job.file.name;
        };
    //xmlhttp.open("GET", "http://{{URI}}:{{Port}}/api/job", true);
    //xmlhttp.setRequestHeader("X-Api-Key", "{{Api-Key}}");
    xmlhttp.open("GET", "localhost:5000/api/job", true);
    xmlhttp.setRequestHeader("X-Api-Key", "1D36DE6AFA40447680E9CAA3C214C671");
                                          
    xmlhttp.send();
}

// https://docs.octoprint.org/en/master/api/printer.html#retrieve-the-current-printer-state
function getPrinterInfo(){
    var xmlhttp = new XMLHttpRequest();


    xmlhttp.onload = function() {

        var reads = JSON.parse(this.responseText);
        console.log(reads);
        document.getElementById("lblbedTemp").innerText = reads.temperature.bed.actual;
        };
    //xmlhttp.open("GET", "http://{{URI}}:{{Port}}/api/printer", true); 
    //xmlhttp.setRequestHeader("X-Api-Key", "{{Api-Key}}");
    xmlhttp.open("GET", "http://localhost:5000/api/printer", true);
    xmlhttp.setRequestHeader("X-Api-Key", "1D36DE6AFA40447680E9CAA3C214C671");
                                          
    xmlhttp.send();
}

$(function() {
    function GCode_Restarter_ViewModel(parameters) {
        var self = this;

        self.controlViewModel = parameters[0];
        self.getAdditionalControls = function() {
            return [{
                'name': 'Reporting', 'children':[
                    {'command': 'M114',
                    'default': '""',
                    'name': 'Get Position',
                    'regex': 'X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)',
                    'template': '"Position: X={0}, Y={1}, Z={2}, E={3}"',
                    'type': 'feedback_command'}
                ]
            }];
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: GCode_Restarter_ViewModel,
        dependencies: [ "controlViewModel" ]
    });
});

__plugin_settings_overlay__ = dict(controls=[dict(children=[dict(command="M114",name="Get Position",
        regex="X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)",
        template="Position: X={0}, Y={1}, Z={2}, E={3}")],name="Reporting_Overlay")])