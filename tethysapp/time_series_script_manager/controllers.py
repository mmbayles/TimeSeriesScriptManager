from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import utilities


@login_required(login_url='/oauth2/login/hydroshare/')
def home(request):
    """
    Controller for the app home page.
    """
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

    context = {

    }

    return render(request, 'time_series_manager/home.html', context)


def parse_data(request):
    json_waterml_data = None
    script_meta = None
    login_status = False
    print "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&"
    if request.user.social_auth.filter(provider='hydroshare'):
        res_ids = request.GET.getlist('res_ids[]')
        src = request.GET.getlist('source[]')[0]
        print src
        print res_ids
        json_waterml_data = []
        for res_id in res_ids:
            json_waterml_data.append(utilities.unzip_waterml(request, res_id, src))
        script_meta = utilities.get_list_hs_scripts(request)
        login_status = True
    else:
        print "Not HydroShare"
    context = {'json_waterml_data': json_waterml_data,
               'scripts': script_meta,
               'login_status': login_status}
    # print request.user.social_auth(provider='hydroshare')

    return JsonResponse(context)

def upload_google(request):
    script_ids = request.GET.getlist('res_ids_script[]')
    variable_names = request.GET.getlist('variables_names[]')
    variable_res_ids = request.GET.getlist('variable_res_ids[]')
    variable_sub_num = request.GET.getlist('variable_sub_num[]')

    # script_name = request.GET.getlist('script_name[]')
    print script_ids
    print variable_names
    print variable_res_ids
    print variable_sub_num
    # print script_name
    for script_id in script_ids:
        script_location = utilities.get_hydro_resource(request, script_id)
        with open(script_location[0]) as f:
            file_data = f.read()
            for idx, val in enumerate(variable_names):
                # val_dates = utilities.parse_waterml(variable_res_ids[idx])

                if 'cuahsi' in variable_res_ids[idx]:
                    source = 'cuahsi'
                else:
                    source = 'hydroshare'

                val_dates = utilities.unzip_waterml(request,variable_res_ids[idx],source,variable_sub_num[idx])
                print val_dates
                print "VAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                val_dates = val_dates[0]


                val1 = val.encode('ascii', 'ignore')
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

def upload_hydroshare(request):
    title = str(request.POST.get('title'))
    abstract = str(request.POST.get('abstract'))
    keywords = str(request.POST.get('keywords'))
    keywords = keywords.split(',')
    # res_access = str(request.POST.get('resAccess'))

    files = request.FILES.getlist('files')
    print request.POST.get('fileUpload')
    print title
    # print files.read()
    for file in files:
        utilities.upload_data_hydroshare(request, file, title, abstract, keywords)
    #
    context = {
        'scripts': 'success'}
    return JsonResponse(context)

def get_hydroshare_list(request):
    hs_list = []
    print "getting hydroshare list"

    hs = utilities.getOAuthHS(request)
    # resource_types = ['CompositeResource','NetcdfResource','TimeSeriesResource']
    resource_types = ['TimeSeriesResource']
    # resource_types = ['CompositeResource']
    resource_list = hs.getResourceList(types=resource_types)
    for resource in resource_list:
        # if resource.resource_type ==''
        print resource
        hs_res_id = resource['resource_id']
        legend = "<div style='text-align:center'><input class = 'checkbox' name = 'res_hydroshare' id =" + hs_res_id+" type='checkbox'>" + "</div>"
        title = resource['resource_title']
        type = resource['resource_type']
        author = resource['creator']
        update = resource['date_last_updated']
        hs_dic = dict(legend=legend,
                      title=title,
                      type=type,
                      author=author,
                      update=update,
                      resource_id=hs_res_id)
        hs_list.append(hs_dic)
    hs_response = dict(error='', data=hs_list)
    return JsonResponse(hs_response)

