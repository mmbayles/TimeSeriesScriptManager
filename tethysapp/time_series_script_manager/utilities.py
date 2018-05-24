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
from suds.transport import TransportError
from suds.client import Client
import urllib2
import collections
import math
import numpy
import sqlite3
from time import mktime as mktime
from netCDF4 import Dataset


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
    resources = hs.getResourceList(full_text_search="#{%Application% Time Series Script Manager}")

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
        script_para = re.findall('#{%(.*)%(.*)}', abstract_txt)
        title = None
        description = None
        variables = []
        title = resource['resource_title']
        for para in script_para:
            if 'Title'in para[0]:
                continue
            elif 'Description' in para[0]:
                description = para[1].strip()
            elif 'Application'in para[0]:
                continue
            else:
                variables.append([para[0].strip(), para[1].strip()])

        script_meta.append({
            'script_name': title,
            'script_des': description,
            'script_res_id': resource['resource_id'],
            'variables': variables
        })
    return script_meta


def unzip_waterml(request, res_id, src, subseries=None):
    temp_dir = get_workspace()
    file_type = None
    data_for_chart = []
    error = ''

    if 'hydroshare' in src:
        hs = getOAuthHS(request)
        file_path_id = get_workspace()
        try:
            hs.getResource(res_id, destination=file_path_id,
                           unzip=True)
            # root_dir = file_path_id + '/' + res_id
            root_dir = os.path.join(file_path_id,res_id)
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
                    elif '.refts.json' in file:
                        file_type = '.json.refts'
                        file_number = parse_ts_layer(path)
                    elif '.sqlite' in file:
                        file_path = path
                        file_type = 'sqlite'
                    elif file.endswith('.nc'):
                        file_path = path
                        file_type='netcdf'
            if file_type is None:
                error = "No supported file type found for resource " + res_id + ". This app supports resource " \
                        "types of HIS Referenced Time Series, Time Series, and Collection with file extension" \
                                                                                " .refts.json"
        except HydroShareNotAuthorized as e:
            print e
            error = 'Current user does not have permission to view this resource'
            # error = str(e)
        except HydroShareNotFound as e:
            print "Resource not found"
            error = 'Resource was not found. Please try again in a few moments'
            # error = str(e)
        except Exception as e:
            print e
            error = str(e)

    elif src == 'cuahsi':
        # get the URL of the remote zipped WaterML resource
        file_type = 'waterml'
        app_host =request.META['HTTP_HOST']
        if 'hs-apps-dev.hydroshare' in app_host:
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
                    file_path = os.path.join(temp_dir, res_id+'.xml')
                    # file_path = temp_dir + '/' + res_id + '.xml'
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

    if error == '':
        if file_type == 'waterml':
            # file_path = utilities.waterml_file_path(res_id,xml_id)
            chart_data = parse_1_0_and_1_1(file_path, res_id, 1)
            data_for_chart.append(chart_data[0])
            error = chart_data[1]
        elif file_type == '.json.refts':
            for i in range(0, file_number):
                # file_path = temp_dir+'/id/timeserieslayer'+str(i)+'.xml'
                file_path = temp_dir + '/timeserieslayer' + str(i) + '.xml'
                if subseries is not None:

                    if float(subseries) == i+1:
                        chart_data = parse_1_0_and_1_1(file_path, res_id, i + 1)
                        data_for_chart.append(chart_data[0])
                        error = chart_data[1]
                else:
                    chart_data = parse_1_0_and_1_1(file_path, res_id, i+1)
                    data_for_chart.append(chart_data[0])
                    error = chart_data[1]
        elif file_type == 'sqlite':
            conn = sqlite3.connect(file_path)
            c = conn.cursor()
            c.execute('SELECT Results.ResultID FROM Results')
            num_series = c.fetchall()
            conn.close()
            for series in num_series:
                if subseries is not None:

                    if float(subseries) == series[0]:
                        str_series = str(series[0])
                        data_for_chart.append(parse_odm2(file_path, str_series, res_id)[0])
                else:
                    str_series = str(series[0])
                    data_for_chart.append(parse_odm2(file_path, str_series, res_id)[0])
        elif file_type == 'netcdf':
            subseries_counter = 1
            dates = []
            dataset = Dataset(file_path)
            try:
                feature_id = dataset.variables['feature_id']
                master_times = collections.OrderedDict()
                dic = 'aaaa'
                master_times.update({dic: []})
                # feature_id = dataset.variables['feature_id']
                dates1 = dataset.variables['time'][:]
                for ele in dates1:
                    n = float(ele)
                    n = n * 60  # time is is minutes not seconds
                    dates.append(n)
                for index, id in enumerate(feature_id):

                        variable = dataset.variables.keys()
                        for sub_var in variable:
                            sub_var_check = sub_var.encode('utf8')

                            if 'streamflow' in sub_var_check or 'velocity' in sub_var_check:
                                if subseries is not None:
                                    if float(subseries) == subseries_counter:
                                        chart_data = parse_netcdf(index, id,
                                                                  dataset.variables[sub_var],
                                                                  res_id, subseries_counter,dates)
                                        data_for_chart.append(chart_data[0])

                                else:
                                    chart_data = parse_netcdf(index, id,
                                                              dataset.variables[sub_var],
                                                              res_id, subseries_counter, dates)
                                    data_for_chart.append(chart_data[0])
                                    error = chart_data[1]
                                subseries_counter = subseries_counter +1

            except:
                error = "Not a valid channel forcing file"
    return data_for_chart


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


def parse_1_0_and_1_1(xml_file_path, res_id, subseries):
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
            return [{
                'organization': organization,
                'site_name': site_name,
                'variable_name': variable_name,
                'units': units,
                'quality': quality,
                'values': values,
                'dates': dates,
                'res_id':res_id,
                'error': error,
                'subseries': subseries
            },
            error]
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
        return [None, data_error]


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


def upload_data_hydroshare(request, file_data, title, abstract, keywords):
    file_name = str(file_data.name)
    file_path = os.path.join(get_user_workspace(request), file_name)
    file_path = file_path.encode(encoding='UTF-8')

    file_text = file_data.read()

    with open(file_path, 'wb') as f:
        f.write(file_text)
    hs = getOAuthHS(request)
    abstract = abstract
    title = title
    keywords = keywords
    rtype = 'CompositeResource'
    # fpath1 = file_path
    # fpath = get_user_workspace(request) + '/' + file_name
    # print fpath
    # print type(fpath)
    # print fpath1
    # print type(fpath1)
    #
    # fpath = '/home/matthew/tethys/src/tethys_apps/tethysapp/time_series_script_manager/workspaces/user_workspaces/mbayles2/High_Low_Flow_Script.ipynb'
    # print fpath
    # print type(fpath)

    # metadata = '[{"coverage":{"type":"period", "value":{"start":"01/01/2000", "end":"12/12/2010"}}}, {"creator":{"name":"John Smith"}}, {"creator":{"name":"Lisa Miller"}}]'
    extra_metadata = '{"Time Series Script Manager": "True"}'
    resource_id = hs.createResource(rtype, title, resource_filename=file_data.name, resource_file=file_path, keywords=keywords, abstract=abstract,
                                    extra_metadata=extra_metadata)
    return resource_id
    # return "d"

def parse_odm2(file_path, result_num,res_id):

    site_name = None
    variable_name = None
    units = None
    organization = None
    quality = None

    values = []
    dates = []
    nodatavalue = None
    conn = sqlite3.connect(file_path)
    c = conn.cursor()
    c.execute(
        'SELECT Variables.VariableNameCV,Units.UnitsName,'
        'Results.SampledMediumCV,Variables.NoDataValue '
        'FROM Results,Variables,Units '
        'WHERE Results.ResultID=' + result_num + ' '
         'AND Results.UnitsID = Units.UnitsID AND Results.VariableID = Variables.VariableID')
    var_unit = c.fetchall()
    for unit in var_unit:
        variable_name = unit[0]
        units = unit[1]
        samplemedium = unit[2]
        nodatavalue = unit[3]
    c.execute(
        'SELECT  TimeSeriesResults.IntendedTimeSpacing, Units.UnitsName,TimeSeriesResults.AggregationStatisticCV '
        'FROM TimeSeriesResults, Units '
        'WHERE TimeSeriesResults.ResultID =' + result_num + ' '
        'AND TimeSeriesResults.IntendedTimeSpacingUnitsID = Units.UnitsID')
    time_support = c.fetchall()
    for time in time_support:
        timeunit = time[1]

        timesupport = time[0]
        datatype = time[2]
    c.execute(
        'SELECT Results.ResultID,Methods.MethodID,Methods.MethodName, '
        'SamplingFeatures.SamplingFeatureName,Actions.ActionTypeCV '
        'FROM Results,FeatureActions,Actions,Methods, SamplingFeatures ' +
        'WHERE Results.ResultID=' + result_num + ' '
                                                 'AND Results.FeatureActionID=FeatureActions.FeatureActionID ' +
        'AND ((FeatureActions.ActionID=Actions.ActionID '
        'AND Actions.MethodID=Methods.MethodID) OR'
        '(FeatureActions.SamplingFeatureID = SamplingFeatures.SamplingFeatureID)) ')
    methods = c.fetchall()  # Returns Result id method id and method description for each result
    # Quality Control
    c.execute(
        'SELECT ProcessingLevels.ProcessingLevelCode, ProcessingLevels.Explanation, ProcessingLevels.Definition '
        'FROM Results, ProcessingLevels ' +
        'WHERE Results.ResultID=' + result_num + ' '
                                                 'AND Results.ProcessingLevelID = ProcessingLevels.ProcessingLevelID')
    qualityControl = c.fetchall()

    c.execute(
        'SELECT Organizations.OrganizationID,Organizations.OrganizationName,Organizations.OrganizationName '
        'FROM Organizations,Affiliations,ActionBy,Actions,FeatureActions,Results ' +
        'WHERE Results.ResultID=' + result_num + ' '
                                                 'AND Results.FeatureActionID=FeatureActions.FeatureActionID ' +
        'AND FeatureActions.ActionID=Actions.ActionID ' +
        'AND Actions.ActionID=ActionBy.ActionID ' +
        'AND ActionBy.AffiliationID = Affiliations.AffiliationID ' +
        'AND Affiliations.OrganizationID = Organizations.OrganizationID ')

    # c.execute('Select *')
    organizations = c.fetchall()

    c.execute(
        'SELECT ResultID,ValueDateTime,DataValue FROM TimeSeriesResultValues')
    data = c.fetchall()
    for ele in data:
        subres_id = ele[0]
        if int(result_num) == subres_id:
            v = ele[2]
            n = ele[1]
            n = ciso8601.parse_datetime(str(n))
            n = n.timetuple()
            n = mktime(n)
            # if v == nodata:
            if v == nodatavalue:
                v = None
            else:
                v = float(v)
            values.append(v)
            dates.append(n)

    error = ''

    conn.close()
    return [{
        'organization': organizations[0][1],
        'site_name': methods[0][3],
        'variable_name': variable_name,
        'units': units,
        'quality': qualityControl[0][0],
        'values': values,
        'dates': dates,
        'res_id': res_id,
        'error': error,
        'subseries':result_num
    },
    error]


def parse_ts_layer(path):
    counter = 0
    error = ''
    response = None
    with open(path, 'r') as f:
        data = f.read()
    data = data.encode(encoding='UTF-8')
    data = data.replace("'", '"')
    json_data = json.loads(data)
    json_data = json_data["timeSeriesReferenceFile"]
    layer = json_data['referencedTimeSeries']

    for sub in layer:

        ref_type = sub['requestInfo']['refType']
        service_type = sub['requestInfo']['serviceType']
        url = sub['requestInfo']['url']
        site_code = sub['site']['siteCode']
        variable_code = sub['variable']['variableCode']
        start_date = sub['beginDate']
        end_date = sub['endDate']
        auth_token = ''
        if ref_type == 'WOF':
            if service_type == 'SOAP':
                if 'nasa' in url:
                    headers = {'content-type': 'text/xml'}
                    body = """<?xml version="1.0" encoding="utf-8"?>
                        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                          <soap:Body>
                            <GetValuesObject xmlns="http://www.cuahsi.org/his/1.0/ws/">
                              <location>""" + site_code + """</location>
                              <variable>""" + variable_code + """</variable>
                              <startDate>""" + start_date + """</startDate>
                              <endDate>""" + end_date + """</endDate>
                              <authToken></authToken>
                            </GetValuesObject>
                          </soap:Body>
                        </soap:Envelope>"""
                    body = body.encode('utf-8')
                    response = requests.post(url, data=body, headers=headers)
                    response = response.content
                else:
                    client = connect_wsdl_url(url)
                    try:
                        response = client.service.GetValues(site_code,
                                                            variable_code,
                                                            start_date,
                                                            end_date,
                                                            auth_token)
                    except:
                        error = "unable to connect to HydroSever"
                        print error
                temp_dir = get_workspace()
                file_path = temp_dir + '/timeserieslayer' + str(counter) + '.xml'
                try:
                    response = response.encode('utf-8')
                except:
                    response = response
                with open(file_path, 'w') as outfile:
                    outfile.write(response)
            if (service_type == 'REST'):
                waterml_url = url + '/GetValueObject'
                response = urllib2.urlopen(waterml_url)
                html = response.read()
            counter = counter + 1
    return counter


def connect_wsdl_url(wsdl_url):
    try:
        client = Client(wsdl_url)
    except TransportError:
        raise Exception('Url not found')
    except ValueError:
        raise Exception(
            'Invalid url')  # ought to be a 400, but no page implemented for that
    except:
        raise Exception("Unexpected error")
    return client


def parse_netcdf(index, id, dataset,res_id,subseries,dates):
    values = []
    site_name = str(id)
    units = dataset.units
    nodatavalue = dataset.missing_value
    variable_name = dataset.long_name
    data = dataset[:]
    for ele in data:
        try:
            v = ele[index]
        except:
            v = ele
        if v == '--':
            v = None
        else:
            try:
                val_float = float(v)
                if val_float == float(nodatavalue):
                    v = None
                elif math.isnan(val_float):
                    v = None
                else:
                    v = val_float
            except:
                v = None
                # records only none null values for running statistics
        values.append(v)

    error = ''

    return [{
        'organization': 'NOAA',
        'site_name': site_name,
        'variable_name': variable_name,
        'units': units,
        'quality': 'Derived products',
        'values': values,
        'dates': dates,
        'res_id': res_id,
        'error': error,
        'subseries':subseries
    },
            error]


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