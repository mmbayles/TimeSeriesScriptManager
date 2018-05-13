from lxml import etree
from .app import TimeSeriesScriptManager
import StringIO
import time
import zipfile
import os
import ciso8601
import requests
import sys
from hs_restclient import HydroShare, HydroShareAuthOAuth2, \
    HydroShareNotAuthorized, HydroShareNotFound
from django.conf import settings
import json
import re


def get_workspace():
    """Get path to Tethys Workspace"""

    return TimeSeriesScriptManager.get_app_workspace().path


def get_user_workspace(request):

    return TimeSeriesScriptManager.get_user_workspace(request.user).path


def get_list_hs_scripts(request):
    # file_path = get_workspace() + '/Test_Resource/test_hs_integration.ipynb'
    # with open(file_path,'r') as file:
    #     file_data = json.loads(file.read())

    hs = getOAuthHS(request)
    # resources = hs.resources(group='Script Group')
    # resources = hs.resources(author='mmbayles@gmail.com')
    # print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    # for res in resources:
    #     print res
    # print "DDDDDDDDDDDDDDDDDDDDDDDDDdd"
    resources = hs.getResourceList(full_text_search="#{%Application% Time Series Script Manager%}")

    # # resources = hs.resources(type ='TimeSeriesResource')
    # resources = hs.resources(type='CompositeResource')
    # # resources = hs.resources(type='CompositeResource')
    # # resources = hs.getResourceList(types ='TimeSeriesResource')
    # # print resources
    # # print dir(resources)
    # re_title = re.compile('(#{%Title%)(.*)(})')
    # re_des = re.compile('(#{%Description%)(.*)(})')
    # re_num = re.compile('(#{%Number_of_Datasets%)(.*)(})')
    # re_vars = re.compile('(#{%)(.*)(%)(.*)(})')
    script_meta = []
    for resource in resources:
        # script_location = get_hydro_resource(request, resource['resource_id'])
        # with open(script_location[0]) as f:
        #     file_data = f.read()
        #     print file_data

        abstract_txt = resource['abstract']
        # re_title = re.compile('\{\w+\}')
        # re_title = re_title.search(abstract_txt)
        # re_des = re_des.search(abstract_txt)
        # re_num = re_num.search(abstract_txt)
        # re_vars = re_vars.search(abstract_txt)
        # print re_vars.group(2)
        script_para = re.findall('#{%(.*)%(.*)}',abstract_txt)
        title = None
        description = None
        variables = []
        for para in script_para:
            if 'Title'in para[0]:
                title = para[1].strip()
            elif 'Description' in para[0]:
                description = para[1].strip()
            elif 'Application'in para[0]:
                continue
            else:
                variables.append([para[0].strip(),para[1].strip()])

        script_meta.append({
            'script_name': title,
            'script_des': description,
            'script_res_id': resource['resource_id'],
            'variables': variables
        })
    return script_meta


def unzip_waterml(request, res_id, src):
    temp_dir = get_workspace()
    file_type = None
    error = ''
    if 'hydroshare' in src:
        hs = getOAuthHS(request)
        file_path_id = get_workspace()
        status = 'running'
        delay = 0
        while status == 'running' or delay < 10:
            if delay > 15:
                error = 'Request timed out. ' + error
                break
            elif status == 'done':
                error = ''
                break
            else:
                try:
                    hs.getResource(res_id, destination=file_path_id,
                                   unzip=True)
                    status = 'done'
                except HydroShareNotAuthorized as e:
                    print e

                    error = 'Current user does not have permission to view this resource'
                    # error = str(e)
                    break
                except HydroShareNotFound as e:
                    print "Resource not found"
                    error = 'Resource was not found. Please try again in a few moments'
                    # error = str(e)
                    time.sleep(2)
                    delay = delay + 1

                except Exception as e:
                    print e
                    print type(e).__name__
                    print e.__class__.__name__
                    error = str(e)
                    status = 'running'
                    time.sleep(2)
                    delay = delay + 1

        if error == '':
            try:
                root_dir = file_path_id + '/' + res_id
                data_dir = root_dir + '/' + res_id + '/data/contents/'
                for subdir, dirs, files in os.walk(root_dir):
                    for file in files:
                        path = data_dir + file
                        if 'wml_1_' in file:
                            file_type = 'waterml'
                            with open(path, 'r') as f:
                                file_data = f.read()
                                f.close()
                                # file_path = temp_dir + '/id/' + res_id + '.xml'
                                file_path = temp_dir + res_id + '.xml'
                                file_temp = open(file_path, 'wb')
                                file_temp.write(file_data)
                        elif '.py' in file:
                            file_type = 'python'
                            with open(path, 'r') as f:
                                file_data = f.read()

                        #         file_temp.close()
                        # elif '.refts.json' in file:
                        #     file_type = '.json.refts'
                        #     file_number = parse_ts_layer(path)
                        # elif '.sqlite' in file:
                        #     file_path = path
                        #     file_type = 'sqlite'
                        # elif file.endswith('.nc'):
                        #     file_path = path
                        #     file_type='netcdf'
                if file_type == None:
                    error = "No supported file type found for resource "+res_id+". This app supports resource types of HIS " \
                            "Referenced Time Series, Time Series, and Collection with file extension .refts.json"
            except Exception as e:
                error = str(e)

    elif src == 'cuahsi':
        # get the URL of the remote zipped WaterML resource
        file_type = 'waterml'
        app_host =request.META['HTTP_HOST']
        if 'appsdev.hydroshare' in app_host:
            url_zip = 'http://qa-hiswebclient.azurewebsites.net/CUAHSI/HydroClient/WaterOneFlowArchive/' + res_id + '/zip'
        else:
            url_zip = 'http://data.cuahsi.org/CUAHSI/HydroClient/WaterOneFlowArchive/' + res_id + '/zip'
        try:
            r = requests.get(url_zip, verify=False)
            z = zipfile.ZipFile(StringIO.StringIO(r.content))
            file_list = z.namelist()
            try:
                for file in file_list:
                    file_data = z.read(file)
                    file_path = temp_dir + '/' + res_id + '.xml'
                    with open(file_path, 'wb') as f:
                        f.write(file_data)
            # error handling
            # checks to see if data is an xml
            except etree.XMLSyntaxError as e:
                print "Error:Not XML"
                error = "Error:Not XML"
            # checks to see if Url is valid
            except ValueError, e:
                print "Error:invalid Url"
                error = "Error:invalid Url"
            # checks to see if xml is formatted correctly
            except TypeError, e:
                error = "Error:string indices must be integers not str"
                print "Error:string indices must be integers not str"
        # check if the zip file is valid
        except zipfile.BadZipfile as e:
            error = "Bad Zip File"
            print error

        except Exception as e:
            print error
            error = str(e)


def get_hydro_resource(request, res_id):
    print 'getting hydroresource'
    temp_dir = get_workspace()
    hs = getOAuthHS(request)
    status = 'running'
    delay = 0
    file_meta = []
    while status == 'running' or delay < 10:
        if delay > 15:
            error = 'Request timed out. ' + error
            break
        elif status == 'done':
            error = ''
            break
        else:
            try:
                hs.getResource(res_id, destination=temp_dir,
                               unzip=True)
                status = 'done'
            except HydroShareNotAuthorized as e:
                print e

                error = 'Current user does not have permission to view this resource'
                # error = str(e)
                break
            except HydroShareNotFound as e:
                print "Resource not found"
                error = 'Resource was not found. Please try again in a few moments'
                # error = str(e)
                time.sleep(2)
                delay = delay + 1

            except Exception as e:
                print e
                print type(e).__name__
                print e.__class__.__name__
                error = str(e)
                status = 'running'
                time.sleep(2)
                delay = delay + 1

    if error == '':
        root_dir = temp_dir + '/' + res_id
        data_dir = temp_dir + '/' + res_id + '/' + res_id + '/data/contents/'
        for subdir, dirs, files in os.walk(root_dir):
            for file in files:
                path = data_dir + file
                if 'wml_1_' in file:
                    file_type = 'waterml'
                    with open(path, 'r') as f:
                        file_data = f.read()
                        f.close()
                        # file_path = temp_dir + '/id/' + res_id + '.xml'
                        file_path = temp_dir + res_id + '.xml'
                        file_temp = open(file_path, 'wb')
                        file_temp.write(file_data)
                        file_temp.close()
                elif '.refts.json' in file:
                    file_type = '.json.refts'
                elif '.sqlite' in file:
                    file_path = path
                    file_type = 'sqlite'
                elif file.endswith('.nc'):
                    file_path = path
                    file_type = 'netcdf'
                elif file.endswith('.ipynb'):
                    file_path = path
                    file_type ='python'
                    return [file_path,file]
                    # file_meta.append({'file_type':file_type,'file_path':file_path})

    # return file_meta

def get_resource_location(res_id):
    temp_dir = get_workspace()

    for subdir, dirs, files in os.walk(temp_dir):
        for file in files:
            path = temp_dir +'/'+ file
            if res_id in file:
                return path

def parse_waterml(res_id):
    temp_dir = get_workspace()
    # file_path = temp_dir + '/Test_Resource/cuahsi_gapfill.py'
    # print file_path
    # with open(file_path, 'r') as f:
    #     file_data = f.read()
    #     print "!!!!!!!!!!!"
    #     print file_data

    file_path = temp_dir + '/'+res_id+'.xml'
    # print file_path
    # with open(file_path, 'r') as f:
    #     file_data = f.read()
    #     print "!!!!!!!!!!!"
    #     print trim(file_data)

    return parse_1_0_and_1_1(file_path,res_id)


def getOAuthHS(request):
    hs_instance_name = "www"
    # hs_instance_name = "beta"
    client_id = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_KEY", None)
    client_secret = getattr(settings, "SOCIAL_AUTH_HYDROSHARE_SECRET", None)
    # this line will throw out from django.core.exceptions.ObjectDoesNotExist if current user is not signed in via HydroShare OAuth
    token = request.user.social_auth.get(provider='hydroshare').extra_data[
        'token_dict']
    hs_hostname = "{0}.hydroshare.org".format(hs_instance_name)
    auth = HydroShareAuthOAuth2(client_id, client_secret, token=token)
    hs = HydroShare(auth=auth, hostname=hs_hostname)
    return hs


def parse_1_0_and_1_1(xml_file_path,res_id):
    """
    Get version of waterml file

    Parameters
    __________
    root: lxml object
        The contents of an xml file that have been parsed using the etree
        method in the lxml library
    Returns
    _______
    site_name
    variable_name
    units
    meta_dic
    organization'
    quality
    method
    status
    datatype
    valuetype
    samplemedium
    timeunit
    sourcedescription
    timesupport
    master_counter
    master_values
    master_times
    master_boxplot
    master_stat'
    master_data_values
    """
    tree = etree.parse(xml_file_path)
    root = tree.getroot()
    root_tag = root.tag.lower()
    nodata = -9999  # default NoData value. The actual NoData value is read from the XML noDataValue tag
    units, site_name, variable_name, quality, method, organization = None, None, None, None, None, None
    values = []
    dates = []
    try:
        if 'timeseriesresponse' in root_tag or 'timeseries' in root_tag or "envelope" in root_tag or 'timeSeriesResponse' in root_tag:

            # lists to store the time-series data
            # iterate through xml document and read all values
            for element in root.iter():
                bracket_lock = -1
                if '}' in element.tag:
                    # print element.tag
                    bracket_lock = element.tag.index(
                        '}')  # The namespace in the tag is enclosed in {}.
                    tag = element.tag[
                          bracket_lock + 1:]  # Takes only actual tag, no namespace

                    if 'value' not in tag:
                        # in the xml there is a unit for the value, then for time. just take the first
                        # print tag
                        if 'unitName' == tag or 'units' == tag or 'UnitName' == tag or 'unitCode' == tag:
                            units = element.text
                        if 'nodatavalue' == tag.lower():
                            nodata = float(element.text)
                        if 'siteName' == tag:
                            site_name = element.text
                        if 'variableName' == tag:
                            variable_name = element.text
                        if 'organization' == tag or 'Organization' == tag or 'siteCode' == tag:
                            try:
                                organization = element.attrib['agencyCode']
                            except:
                                organization = element.text
                        if "qualitycontrollevel" == tag.lower():
                            quality = element.attrib['qualityControlLevelID']

                    elif 'value' == tag:
                        n = element.attrib['dateTime']
                        n = ciso8601.parse_datetime(n)
                        n = n.timetuple()
                        n = time.mktime(n)
                        dates.append(n)

                        v = element.text
                        if float(v) == nodata:
                            v = None
                        else:
                            v = float(element.text)
                        values.append(v)

            error = ''
            return {
                'organization': organization,
                'site_name': site_name,
                'variable_name': variable_name,
                'units': units,
                'quality': quality,
                'values': values,
                'dates': dates,
                'res_id':res_id,
                'error': error
            }
        else:
            parse_error = "Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series"
            # error_report(
            #     "Parsing error: The WaterML document doesn't appear to be a WaterML 1.0/1.1 time series")
            print parse_error
            return [None,parse_error]
    except Exception, e:
        data_error = "Parsing error: The Data in the Url, or in the request, was not correctly formatted for water ml 1."
        # error_report(
        #     "Parsing error: The Data in the Url, or in the request, was not correctly formatted.")
        print data_error
        print e
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return [None,data_error]


def ipynb_formatter(data):
    pynotebook = json.loads(data)
    pynotebook = pynotebook['cells']
    text = ''
    for cell in pynotebook:
        for line in cell['source']:
            if cell['cell_type']=='markdown':
                if line[0] != '#':
                    line = '#'+line
            text = text + line
            if "\n" not in line:
                text = text+'\n'
        text = text + '\n'
    return text