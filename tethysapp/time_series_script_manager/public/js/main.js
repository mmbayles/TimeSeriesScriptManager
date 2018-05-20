var number = 0;
// var CLIENT_ID = '289897672263-nba5onfn04b7k36u620i2ipthtnq8hds.apps.googleusercontent.com';
var CLIENT_ID = '289897672263-9t2rqp7l3llo9oggach2sgu7idr3iqt1.apps.googleusercontent.com';

// var API_KEY = 'AIzaSyB96S1nc9Rr0vEVXDsfYE9_hfWOLmMsueA';
var API_KEY = 'AIzaSyAutdvQuacRMlAUeVGueeEOSi9d1_A2kUI';
var DISCOVERY_DOCS = ["https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"];
var SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive.file';
$(document).ready(function () {
    $("#divViewScript").hide()
    console.log("ready");
    handleClientLoad();
    // Handle script selection and display
    $("#sel1").click(function(){
        $("#scriptVar").text("");
         var table = $('#data_table').DataTable();
        var table_len = table.page.len();

        table.page.len(-1);
        table.draw();

        for (var i = 0, len = number; i < len;i++){
                $("#"+i).html($("<option></option>")
                    .text("Please Select a Script\n")
                    .attr("value", "None")
                );
        }
            $("#divViewScript").hide()

        $("#scriptDescription").text($("#sel1 :selected").attr('description'));
        var scriptVariables = $("#sel1 :selected").attr('variables').split(",");
        if (scriptVariables.length >1) {
                $("#divViewScript").show()

            //  $("#divViewScript").html('<button type="button" class="btn btn-info" name="'+ $("#sel1 :selected").attr('res_id')+'"style="float: left; position:relative" onclick="viewScript(this.name)">\n' +
            // 'View Script\n' +
            // '</button>')
            $("#divViewScript").attr('name',$("#sel1 :selected").attr('res_id'))
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
         table.page.len(table_len);
        table.draw();
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
             {
                "name":"viewRes",
                "className": "viewRes",
                "data": "resource"
            },
        ],
        "order": [[1, 'asc']]
    });
    $('#hs_resource_table').DataTable({
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "scrollY":true,
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
            var table = $('#hs_resource_table').DataTable();
            table.$('td').tooltip({
                selector: '[data-toggle="tooltip"]',
                container: 'body',
                "delay": 0,
                "track": true,
                "fade": 100
            });
        },


        "columns": [
             {
                "name":"legend",
                "className": "legend",
                "data": "legend"
            },
            {"data": "title"},
            {"data": "type"},
            {"data": "author"},
            {"data": "update"},
            //{"data":"download"}
        ],
        "order": [[1, 'asc']]
    });
    document.title = 'Time Series Script Manager';
    var source =find_query_parameter('Source');
    var res_ids =find_query_parameter('WofUri');

    if (source.length == 0){
        source=['hydroshare']
    }
    if (res_ids.length == 0){
        res_ids = find_query_parameter('res_id')
    }
    ajax_get_data(source, res_ids)
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


function ajax_get_data(source, res_ids){

    console.log(source);
    $.ajax({
            type: "GET",
        crossDomain: true,
            data: {
                "res_ids":res_ids,
                "source":source
            },
            url: 'parse_data',
            success: function (json_data) {
                if (json_data.login_status == false){
                    var newWin = window.open("/oauth2/login/hydroshare/?next=/apps/time-series-script-manager/?src=cuahsi&WofUri=cuahsi-wdc-2018-05-16-71934608", '_self');
                }
                else{
                    console.log(json_data)
                    addDataToTable(json_data.json_waterml_data);
                    addScriptToList(json_data.scripts)
                }


            },
            error: function () {
                console.log('error')
            }
    });

}
function addDataToTable(data){
    var table = $('#data_table').DataTable();//defines the primary table
    // table
    //     .clear()
    //     .draw();

    for (series in data){

        for (subseries in data[series]){
            var data_path = data[series][subseries]
            // var legend = "<div style='text-align:center'><input name ="+data[series]["res_id"]+" class = 'checkbox' id =" + number +" type='checkbox' onClick ='series_visiblity_toggle(this.id,this.name);' checked>" + "</div>"
            var legend = "<div style='text-align:center'><select prev ='None' name ="+data_path["res_id"]+" class = 'form-control table-control' id =" + number +" subSeries="+data_path["subseries"]+" ></div>";
            if (data_path["res_id"].indexOf('cuahsi') >-1 ){
                view = "?Source=cuahsi&WofUri="+data_path["res_id"]
            }
            else{
                view = "hydroshare/?src=hydroshare&res_id="+data_path["res_id"]
            }
            var dataset = {
                legend: legend,
                organization: data_path["organization"],
                name: data_path["site_name"],
                variable: data_path["variable_name"],
                unit: data_path["units"],
                quality:data_path["quality"],
                count: data_path["values"].length,
                resource:'<a id="myLink" href="/apps/timeseries-viewer/'+view+'" target="_blank">View Resource</a>'
            };
            table.row.add(dataset).draw();
            number = number + 1
        }

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
    var variable_sub_num = []
    // var res_ids_script = [];

    var table = $('#data_table').DataTable();
    var table_len = table.page.len();

    table.page.len(-1);
    table.draw();
    // table.page.len(table_len);
    // table.draw();
    for (var i = 0, len = number; i < len;i++){
        var seriesValue = $("#"+i+" :selected").attr("value");
        console.log(seriesValue !== "None")
        if (seriesValue !== "None"){
            console.log('Not none')
            variable_names.push(seriesValue);
            variable_res_ids.push($("#"+i).attr("name"))
            variable_sub_num.push($("#"+i).attr("subseries"))
        }
    }
    var res_ids_script=[$("#sel1 :selected").attr('res_id')];
    // Validation to ensure script selected and that correct number of variables have been assigned
    if (res_ids_script == ""){
        alert("Please choose a script");
        return
    }
    console.log(variable_names)
    if ($('#0 option').size()-1 != variable_names.length){
         alert("Please select a time series for each listed variable");
        return
    }
    table.page.len(table_len);
    table.draw();
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
                    "res_ids_script":res_ids_script,
                    "variable_sub_num":variable_sub_num
                },
                url: '/apps/time-series-script-manager/upload_google',
                success: function (json_data) {
                    console.log(json_data);
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
                $('#view-script-modal').modal('show');
                $("#scriptViewer").text(json_data['scripts'])
                // $("#view-script-modal-label").text($("#sel1 :selected").text()+".ipynb")

            },
            error: function () {
                console.log('error')
            }
        });
}


function uploadHydroShare(){
    var csrf_token = getCookie('csrftoken');
     var files = document.getElementById("input-files").files[0];
     var form = new FormData();
      form.append("title", $('#resTitle').val());
      form.append("abstract", $('#resAbstract').val());
      form.append("keywords", $('#resKeywords').val());
      form.append("accessType", "testomg");
      form.append("files", files);
      console.log(form);
   $.ajax({
        type: "POST",
        headers: {'X-CSRFToken': csrf_token},
        dataType: 'json',
        processData: false,
        contentType: false,
        data: form,
        url: '/apps/time-series-script-manager/upload_hydroshare/',
        success: function (json_data) {
            console.log(json_data)

        },
        error: function () {
            console.log('error')
        }
    });
}
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function get_list_hs_res(){
    console.log('get hs resources')

    var hs_res_list_loaded = false
    hs_res_ids =''
    // hs_res_list_loaded = true
    if (hs_res_list_loaded == false) {
        setTimeout(function(){
            console.log('resize')
            $(window).trigger("resize");
            }, 500);
        $('#hs_resource_table_wrapper').hide();
        var csrf_token = getCookie('csrftoken');
        data_url ="/apps/time-series-script-manager/get_hydroshare_list/";
        $.ajax({
            type: "POST",
            headers: {'X-CSRFToken': csrf_token},
            dataType: 'json',
            //timeout: 5000,
            data: {'hs_res_ids': hs_res_ids,
                    'source':"hydroshare"
            },
            url: data_url,
            success: function (json) {
                    var table_hs = $('#hs_resource_table').DataTable();//defines the primary table
                    // console.log(row_tracker)
                    json = json.data
                    console.log(json)
                    len = json.length
                    for (series in json) {
                        table_hs.row.add(json[series]).draw();
                    }
                    $('#loading_hs').hide();
                    $('#hs_resource_table_wrapper').show();
                    $(window).resize()
                    hs_res_list_loaded = true
            },
            error: function () {
                show_error("Error loading HydroShare Resources");
            }
        });
    }



}

function getAddHS(){
    var table = $('#hs_resource_table').DataTable();
    var addHSResources = [];
    var table_len = table.page.len();

    table.page.len(-1);
    table.draw();
    for (var i = 0, len = table.rows().data().length; i < len;i++) {
        var row_up = table.rows().data()[i];
        var resource_id = row_up.resource_id
        if ($("#"+resource_id).is(":checked")) {
            console.log("Its checked")
            addHSResources.push(resource_id)
        }
    }
    table.page.len(table_len);
    table.draw();
    ajax_get_data(['hydroshare'], addHSResources)
}