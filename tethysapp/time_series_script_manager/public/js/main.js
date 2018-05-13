var number = 0;
var CLIENT_ID = '';
var API_KEY = '';
var DISCOVERY_DOCS = ["https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"];
var SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive.file';

$(document).ready(function () {
    console.log("ready");
    handleClientLoad();

    // Handle script selection and display
    $("#sel1").click(function(){
        $("#scriptVar").text("");
        for (var i = 0, len = number; i < len;i++){
                $("#"+i).html($("<option></option>")
                    .text("Please Select a Script\n")
                    .attr("value", "None")
                );
        }
        $("#divViewScript").html('<div id = "divViewScript">\n' +
            '<button type="button" class="btn btn-info" name="'+ $("#sel1 :selected").attr('res_id')+'"style="float: left; position:relative" onclick="viewScript(this.name)">\n' +
            'View Script\n' +
            '</button>')
        $("#scriptDescription").text($("#sel1 :selected").attr('description'));
        var scriptVariables = $("#sel1 :selected").attr('variables').split(",");
        if (scriptVariables.length >1) {
            for (var i = 0, len = scriptVariables.length; i < len;) {
                $("#scriptVar").append("<li>"+scriptVariables[i].bold() + " : " + scriptVariables[i + 1]+"</li><li></li>");

                for (var j = 0; j < number; j++) {
                    $("#" + j).append($("<option></option>")
                        .text(scriptVariables[i]+"\n")
                        .attr("value", scriptVariables[i])
                    );
                }
                i = i + 2;
            }

        }
    });

    $('#data_table').DataTable({
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "searching":false,

        "createdRow": function (row, data, dataIndex) {
            var col_counter = 0
            columns =
            this.api().columns().every( function () {
                if (col_counter >1){

                    var column = this;
                    var select = $('<select style="width: 100% !important;"><option value="" selected >Show All: '+this.title()+'</option></select>')
                        .appendTo( $(column.footer()).empty() )
                        .on( 'change', function () {
                            var val = $.fn.dataTable.util.escapeRegex(
                                $(this).val()
                            );
                            column
                                .search( val ? '^'+val+'$' : '', true, false )
                                .draw();
                        } );

                    column.data().unique().sort().each( function ( d, j ) {
                        select.append( '<option value="'+d+'">'+d+'</option>' )
                    } );
                }

                col_counter = col_counter +1
            } );
        },

        "columns": [
            {
                "name":"legend",
                "className": "legend",
                "data": "legend"
            },

            {"data": "organization"},
            {"data": "name"},
            {"data": "variable"},
            {"data": "unit"},
            {"data": "quality"},
            {"data": "count"},
        ],
        "order": [[1, 'asc']]
    });

    document.title = 'Time Series Script Manager';

    ajax_get_data()
});

function handleClientLoad() {
    gapi.load('client:auth2', initClient);
}
/**
 *  Initializes the API client library and sets up sign-in state
 *  listeners.
 */

function initClient() {
    gapi.client.init({
        apiKey: API_KEY,
        clientId: CLIENT_ID,
        discoveryDocs: DISCOVERY_DOCS,
        scope: SCOPES
    }).then(function () {
        console.log('sign in changed')
        // Listen for sign-in state changes.
        gapi.auth2.getAuthInstance().isSignedIn.listen(updateSigninStatus);
    });
}

/**
 *  Called when the signed in status changes, to update the UI
 *  appropriately. After a sign-in, the API is called.
 */
function updateSigninStatus(isSignedIn) {
    if (isSignedIn) {
        console.log('user is signe in to google account')
        uploadToGoogle()
    }
}



function find_query_parameter(name) {
    url = location.href;
    values=[]
    url1 = url.split('?')
    if (url1[1]==undefined){values.push('')}
    else {
        url1 = url1[1].split('&')
        for (e in url1) {
            if (url1[e].indexOf(name) == 0) {
                string = url1[e]
                string = string.split('=')
                values.push(string[1])
            }
        }
    }
    return values
}


function ajax_get_data(){
    var res_ids =find_query_parameter('WofUri');
    $.ajax({
            type: "GET",
        crossDomain: true,
            data: {
                "res_ids":res_ids,
            },
            url: 'parse_data',
            success: function (json_data) {
                console.log(json_data)
                addDataToTable(json_data.data,json_data.scripts);
                addScriptToList(json_data.scripts)
            },
            error: function () {
                console.log('error')
            }
    });

}
function addDataToTable(data,script){
    number = 0;
    var table = $('#data_table').DataTable();//defines the primary table
    table
        .clear()
        .draw();
    console.log(data)
    for (series in data){
        // var legend = "<div style='text-align:center'><input name ="+data[series]["res_id"]+" class = 'checkbox' id =" + number +" type='checkbox' onClick ='series_visiblity_toggle(this.id,this.name);' checked>" + "</div>"
        var legend = "<div style='text-align:center'><select prev ='None' name ="+data[series]["res_id"]+" class = 'form-control table-control' id =" + number +" ></div>";

        var dataset = {
            legend: legend,
            organization: data[series]["organization"],
            name: data[series]["site_name"],
            variable: data[series]["variable_name"],
            unit: data[series]["units"],
            quality:data[series]["quality"],
            count: data[series]["values"].length,
        };
        table.row.add(dataset).draw();
        number = number + 1
    }
    for (var i = 0, len = number; i < len;i++){
        $("#"+i).append($("<option></option>")
            .text("Please Select a Script\n")
            .attr("value", "None")
            // .attr("prev", "None")
        );
    }
    $('.table-control').click(function() {
        // get previous selection value to enable selection
        var selectedVar = $("#"+this.id+" :selected").attr("value");
        var previousVar = $("#"+this.id).attr("prev");

        $("#"+this.id).attr("prev",selectedVar);
        // Enable past selection
        $( ".table-control [value='"+previousVar+"']" ).removeAttr('disabled');
        // Disable current selection
        $( ".table-control [value='"+selectedVar+"']" ).attr('disabled','disabled');
        // Make sure default selection is always enabled
        $( ".table-control [value='None']" ).removeAttr('disabled');
    });

}

function addScriptToList(script_list){
    $("#sel1").html('')
    $("#sel1").append($("<option></option>")
        .text("Please Select a Script")
        .attr("description", "")
        .attr("variables","" )
        .attr("res_id","" )
    );

    for (script in script_list){
         $("#sel1").append($("<option></option>")
             .text(script_list[script]['script_name'])
             .attr("description", script_list[script]['script_des'])
             .attr("variables", script_list[script]['variables'].join())
             // .attr("script_res_num", script_list[script]['script_res_num'])
             .attr("res_id", script_list[script]['script_res_id'])
         )

    }
}

function uploadToGoogle(){

     var variable_names =[];
        var variable_res_ids =[];
        // var res_ids_script = [];

        for (var i = 0, len = number; i < len;i++){
            var seriesValue = $("#"+i+" :selected").attr("value");
            if (seriesValue !== "None"){
                variable_names.push(seriesValue);
                variable_res_ids.push($("#"+i).attr("name"))
            }
        }
    var res_ids_script=[$("#sel1 :selected").attr('res_id')];
    // Validation to ensure script selected and that correct number of variables have been assigned
    if (res_ids_script == ""){
        alert("Please choose a script");
        return
    }
    if ($('#0 option').size()-1 != variable_names.length){
         alert("Please select a time series for each listed variable");
        return
    }
    // Check if user is signed in.
    var isSignedGoogle = gapi.auth2.getAuthInstance().isSignedIn.get();
    // If signed in create script
    if (isSignedGoogle){
        console.log ('Launching ajax');

        $.ajax({
                type: "GET",
                data: {
                    "variable_res_ids":variable_res_ids,
                    "variables_names":variable_names,
                    "res_ids_script":res_ids_script
                },
                url: '/apps/time-series-script-manager/upload_google',
                success: function (json_data) {
                    console.log(json_data)
                    createFolder(json_data['data'],$("#sel1 :selected").text()+".ipynb")
                },
                error: function () {
                    console.log('error')
                }
        });
    }
    // If not signed in open Google sign in window
    else{
        gapi.auth2.getAuthInstance().signIn();
    }
}


function createFolder(data,file_name){
    var fileExisting = null;
    gapi.client.drive.files.list({
        'fields': "nextPageToken, files(id, name)",
        'mimeType':"application/vnd.google-apps.folder",
    }).then(function(response) {
        var files = response.result.files;
        if (files && files.length > 0) {
            for (var i = 0; i < files.length; i++) {
                if (files[i].name == "Time Series Script Manager"){
                    fileExisting = files[i];
                    console.log(fileExisting.name + ' (' + fileExisting.id + ')');
                }
            }
        } else {
            console.log('No files found.');
        }

        console.log(fileExisting);
        if (fileExisting==null){
            console.log("Creating new folder");
            var fileMetadata = {
            'name' : 'Time Series Script Manager',
            'mimeType' : 'application/vnd.google-apps.folder',
            // 'parents': [parentId]
            };
            gapi.client.drive.files.create({
                resource: fileMetadata,
            }).then(function(response) {
                switch(response.status){
                    case 200:
                        var file = response.result;
                        console.log('Created Folder Id: ', file.id);
                        createFile(file_name,data,file,openScript)
                        break;
                    default:
                        console.log('Error creating the folder, '+response);
                        break;
                }
            });

        }
        else{
            createFile(file_name,data,fileExisting.id)
        }

    });
}


function createFile(name,data,folderId,callback) {
    const boundary = '-------314159265358979323846';
    const delimiter = "\r\n--" + boundary + "\r\n";
    const close_delim = "\r\n--" + boundary + "--";

    const contentType = 'application/json';

    var metadata = {
        'name': name,
        'mimeType': contentType,
        'parents':[folderId]
    };

    var multipartRequestBody =
        delimiter +
        'Content-Type: application/json\r\n\r\n' +
        JSON.stringify(metadata) +
        delimiter +
        'Content-Type: ' + contentType + '\r\n\r\n' +
        data +
        close_delim;

    var request = gapi.client.request({
        'path': '/upload/drive/v3/files',
        'method': 'POST',
        'params': {'uploadType': 'multipart'},
        'headers': {
            'Content-Type': 'multipart/related; boundary="' + boundary + '"'
        },
        'body': multipartRequestBody});
    if (!callback) {
        callback = function(file) {
            console.log(file);
            // Might not open automatically depending on users pop up settings
            // TODO make note of this is the documentation
            window.open('https://colab.research.google.com/drive/'+file.id,'_blank')
        };
    }
    request.execute(callback);
}


function viewScript(res_id){
     $.ajax({
            type: "GET",
            data: {
                "res_id":[res_id]
            },
            url: '/apps/time-series-script-manager/view_script',
            success: function (json_data) {
                console.log(json_data)
                         $('#help-modal').modal('show');

                $("#scriptViewer").text(json_data['scripts'])
                $("#help-modal-label").text($("#sel1 :selected").text()+".ipynb")

            },
            error: function () {
                console.log('error')
            }
        });
}