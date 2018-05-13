from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import utilities
@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    print "hydroshare"
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11"
    res_ids = request.GET.getlist('WofUri')
    cuahsi_src = request.GET.getlist('Source')
    hydroshare_src = request.GET.getlist('src')
    print hydroshare_src
    if hydroshare_src == 'hydroshare':
        src = 'hydroshare'
    else:
        src = 'cuahsi'
    for res_id in res_ids:
        utilities.unzip_waterml(request, res_id, src)
    print res_ids
    print src


    context = {

    }

    return render(request, 'time_series_manager/main.html', context)


def parse_data(request):
    res_ids = request.GET.getlist('res_ids[]')
    json_data = []
    for res_id in res_ids:
        utilities.unzip_waterml(request, res_id, 'cuahsi')
        json_data.append(utilities.parse_waterml(res_id))
    script_meta = utilities.get_list_hs_scripts(request)


    # utilities.google_test()
    context = {'data': json_data,
               'scripts': script_meta}
    return JsonResponse(context)

def upload_google(request):
    script_ids = request.GET.getlist('res_ids_script[]')
    variable_names = request.GET.getlist('variables_names[]')
    variable_res_ids = request.GET.getlist('variable_res_ids[]')
    # script_name = request.GET.getlist('script_name[]')
    print script_ids
    print variable_names
    print variable_res_ids
    # print script_name
    for script_id in script_ids:
        script_location = utilities.get_hydro_resource(request, script_id)
        with open(script_location[0]) as f:
            file_data = f.read()
            for idx, val in enumerate(variable_names):
                val_dates = utilities.parse_waterml(variable_res_ids[idx])
                val1 = val.encode('ascii','ignore')
                # file_data.replace(val+"_values = None", val+"_values = "+val_dates['values'])
                file_data = file_data.replace(val1+'_values = None', val1+'_values = [%s]' % ', '.join(map(str, val_dates['values'])))
                # file_data = file_data.replace('TimeSeries1_values', 'Testing 123344444')
                file_data = file_data.replace(val1+'_dates = None', val1+'_dates = [%s]' % ', '.join(map(str, val_dates['dates'])))
        user_workspace = utilities.get_user_workspace(request)
        file_path = user_workspace + '/' + script_location[1]
        with open(file_path, 'wb') as f:
            f.write(file_data)
    # for data_id in data_ids:
    #     resource_location = utilities.get_resource_location(data_id)
    #     print resource_location
    # print script_location.encode('ascii','ignore')
    # print type(script_location.encode('ascii','ignore'))
    # print type(resource_location)
    # utilities.create_hydro_resource(request, script_location.encode('ascii','ignore'),resource_location)
    context = {'data': file_data
               }
    return JsonResponse(context)

def view_script(request):
    res_id = request.GET.getlist('res_id[]')
    print res_id
    script_location = utilities.get_hydro_resource(request, res_id[0])
    with open(script_location[0]) as f:
        file_data = f.read()
        file_data = utilities.ipynb_formatter(file_data)
    print file_data
    print res_id
    context = {
        'scripts': file_data}
    return JsonResponse(context)