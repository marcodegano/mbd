import csv
import datetime
import mysql.connector
import os
import json
from config import *

############################################################################################################
#Writes the passed Array into a .csv file
############################################################################################################
def writeCSV(errors, file):
 
    deleteFileifExist(file)
    
    with open(file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
            
        csv_writer.writerow(['Client Name', 'Client ID', 'BranchID', 'Account Manager', 'Location Name', 'Location Address', 'Work Order ID', 'Error Message', 'Directory', 'Location ID', 'Directory ID', 'Error Date'])
        
        for error in errors:
             csv_writer.writerow([error[0],error[1],error[2],error[3],error[4],error[5],error[6], str(error[7]).replace('<font color="green">', ''),error[8],error[10],error[11],error[12]])

        print("CSV Created!")
        
############################################################################################################
#Searches for a file and deletes it.
############################################################################################################
def deleteFileifExist(filepath):
    # As file at filePath is deleted now, so we should check if file exists or not not before deleting them
    if os.path.exists(filepath):
        os.remove(filepath)
        print("Previous report deleted")
    else:
        print("Cannot delete the file as it doesn't exist")
        
############################################################################################################
#fetches all the API errors from WOMS DB
############################################################################################################
def getAPIErrors(SQLfile):
    from mysql.connector import Error

    # Open and read the file as a single buffer
    fd = open(SQLfile, 'r')
    SQLQuery = fd.read()
    fd.close()
    
    apierrors = []
    
    print("Fetching API Errors...")
    try:
        mySQLconnection = config.getwomsdbconnection()
            
        cursor = mySQLconnection.cursor()
        cursor.execute(SQLQuery)
        
        apierrors = cursor.fetchall()
        
    except Error as e :
        print ("Error while connecting to MySQL", e)
    finally:
        #closing database connection.
        if(mySQLconnection.is_connected()):
            mySQLconnection.close()
            print("MySQL connection is closed")
        
    return apierrors

############################################################################################################
#Seperates the Community failed Work Orders from the true API errors
############################################################################################################
def filtercommunity(fullerrors):
    
    community = []
    api = []
    
    for error in fullerrors:
        
        if 'font color="green"' in error[7]:
            community.append(error)
        else:
            api.append(error)
            
    return [community, api]
    
############################################################################################################
#Parse the different API Errors into English
############################################################################################################
def parseerrors(rawerrors):

    #from bson.json_util import dumps
    englishOPS = []
    englishSRE = []
    
    for err in rawerrors:
    
        englishmessage = ''
        
        error = ' '.join(str(err[7]).split()).replace('\\n','').replace('\\t','').replace('\\r','')
        englishmessage = error
        
        if err[11] == 1:
            #t=1
            formatted = formatbingerror(error, englishmessage)
            englishmessage = formatted[0]
            team = formatted[1]
         
        elif err[11] == 29 or err[11] == 88:
            #t=1
            formatted = formathotfrogerror(error, englishmessage)
            englishmessage = formatted[0]
            team = formatted[1]
        
        elif err[11] == 48:
            #t=1
            formatted = formatshowmelocalerror(error, englishmessage)
            englishmessage = formatted[0]
            team = formatted[1]
            
        elif err[11] == 37 or err[11] == 176:
            #t=1
            formatted = formatn49error(error, englishmessage)
            englishmessage = formatted[0]
            team = formatted[1]
            
        elif err[11] == 158:
            #t=1
            formatted = formatinfogrouperror(error, englishmessage)
            englishmessage = formatted[0]
            team = formatted[1]
            
        print(englishmessage)
        if team == 'OPS':
            englishOPS.append([err[0],err[1],err[2],err[3],' '.join(str(err[4]).split()),' '.join(str(err[5]).split()),err[6],englishmessage,err[8],err[9],err[10],err[11],err[12]])
        elif team == 'SRE':
            englishSRE.append([err[0],err[1],err[2],err[3],' '.join(str(err[4]).split()),' '.join(str(err[5]).split()),err[6],englishmessage,err[8],err[9],err[10],err[11],err[12]])
            
    return [englishOPS,englishSRE]

############################################################################################################
#Execution starts here.
############################################################################################################
def main():

    from datetime import timedelta
    from datetime import date
    
    today = date.today()
    
    SQLfile = 'APIErrors.sql'
    errors = getAPIErrors(SQLfile)

    if len(errors) > 0:
        print(len(errors))
        filtered = filtercommunity(errors)
        
        communityerrors = filtered[0]
        apierrors = filtered[1]
        
        englisherrors = parseerrors(apierrors)
        OPSErrors = englisherrors[0]
        SREErrors = englisherrors[1]
        
        print(str(len(communityerrors)) + " Community API Errors")
        print(str(len(apierrors)) + " API Errors")
        
        writeCSV(communityerrors, 'Archive/Community API Errors - ' + str(today) + '.csv')
        writeCSV(OPSErrors, 'Archive/OPS API Errors - ' + str(today) + '.csv')
        writeCSV(SREErrors, 'Archive/SRE API Errors - ' + str(today) + '.csv')
        
    else:
        print("No errors returned!")
    


############################################################################################################
#Returns a formatted version of the RAW Infogroup error
############################################################################################################
def formatinfogrouperror(error, englishmessage):

    if 'Failed to get listing_state' in error:
        englishmessage = 'Failed to get listing_state'
        team = 'SRE'
    
    elif 'Unexpected error occurred.' in error:
        englishmessage = 'Unexpected error occurred.'
        team = 'SRE'
        
    elif 'listing_state_options' in error:
        englishmessage = 'listing_state_options'
        team = 'SRE'
        
    elif '"statusCode":409' in error:
        englishmessage = 'statusCode:409'
        team = 'SRE'
        
    elif 'listing_status' in error:
        englishmessage = 'Application Error'
        team = 'SRE'
        
    elif 'ECONNRESET' in error:
        englishmessage = 'TCP Connection reset'
        team = 'SRE'
        
    elif 'submit_id' in error:
        englishmessage = 'Cannot read property "submit_id"'
        team = 'SRE'

    else:
        team = 'OPS'
        
        RAW = str(error).replace('"', '')
        RAW = RAW.replace("'",'"').replace('"{','{').replace('}"','}')
        RAW = RAW.replace('err:','"err":')
        RAW = RAW.replace('{ zip:','{ "zip":').replace('{ state:','{ "state":').replace('{ phone:','{ "phone":').replace('{ professional_first_name:','{ "professional_first_name":')
        RAW = RAW.replace('{ additional_phone:','{ "additional_phone":').replace('{ street:','{ "street":').replace('{ last_name:','{ "last_name":').replace('{ first_name:','{ "first_name":')
        RAW = RAW.replace('], zip:','], "zip":').replace('], state:','], "state":').replace('], phone:','], "phone":').replace('], professional_first_name:','], "professional_first_name":')
        RAW = RAW.replace('], additional_phone:','], "additional_phone":').replace('], street:','], "street":').replace('], last_name:','], "last_name":').replace('], first_name:','], "first_name":')
        RAW = RAW.replace('{ email_address:','{ "email_address":').replace('{ primary_sic_code_id:','{ "primary_sic_code_id":').replace('{ sic_code_ids_2:','{ "sic_code_ids_2":')
        RAW = RAW.replace('], email_address:','], "email_address":').replace('], primary_sic_code_id:','], "primary_sic_code_id":').replace('], sic_code_ids_2:','], "sic_code_ids_2":')
        RAW = RAW.replace('{ operating_hours:','{ "operating_hours":').replace('{ name:','{ "name":').replace('{ company_description:','{ "company_description":').replace('{ sic_code_ids_3:','{ "sic_code_ids_3":')
        RAW = RAW.replace('], operating_hours:','], "operating_hours":').replace('], name:','], "name":').replace('], company_description:','], "company_description":').replace('], sic_code_ids_3:','], "sic_code_ids_3":')
        RAW = RAW.replace('{ sic_code_ids_4:','{ "sic_code_ids_4":').replace('{ sic_code_ids_5:','{ "sic_code_ids_5":').replace('{ professional_last_name:','{ "professional_last_name":')
        RAW = RAW.replace('], sic_code_ids_4:','], "sic_code_ids_4":').replace('], sic_code_ids_5:','], "sic_code_ids_5":').replace('], professional_last_name:','], "professional_last_name":')
        RAW = RAW.replace('{ website:','{ "website":').replace('{ professional_email:','{ "professional_email":').replace('{ categories:','{ "categories":').replace('{ loc_bizcontact:','{ "loc_bizcontact":')
        RAW = RAW.replace('], website:','], "website":').replace('], professional_email:','], "professional_email":').replace('], categories:','], "categories":').replace('], loc_bizcontact:','], "loc_bizcontact":')
        RAW = RAW.replace(', warning:',', "warning":').replace('\\','').replace('"|"','|').replace('"""','"')
        
        print(RAW)
        temp = json.loads(RAW)
        print(temp)
        
        if '"err":' in RAW:
            englishmessage = temp['API Push Failed']['err']
        elif '"street":' in RAW:
            englishmessage = temp['API Push Failed']['street'][0]
        elif '"last_name":' in RAW:
            englishmessage = temp['API Push Failed']['last_name'][0]
        elif '"first_name":' in RAW:
            englishmessage = temp['API Push Failed']['first_name'][0]
        elif '"zip":' in RAW:
            englishmessage = temp['API Push Failed']['zip'][0]
        elif '"state":' in RAW:
            englishmessage = temp['API Push Failed']['state'][0]
        elif '"additional_phone":' in RAW:
            englishmessage = temp['API Push Failed']['additional_phone'][0]
        elif '"professional_first_name":' in RAW:
            englishmessage = temp['API Push Failed']['professional_first_name'][0]
        elif '"email_address":' in RAW:
            englishmessage = temp['API Push Failed']['email_address'][0]
        elif '"primary_sic_code_id":' in RAW:
            englishmessage = temp['API Push Failed']['primary_sic_code_id'][0]
        elif '"sic_code_ids_2":' in RAW:
            englishmessage = temp['API Push Failed']['sic_code_ids_2'][0]
        elif '"sic_code_ids_3":' in RAW:
            englishmessage = temp['API Push Failed']['sic_code_ids_3'][0]
        elif '"sic_code_ids_4":' in RAW:
            englishmessage = temp['API Push Failed']['sic_code_ids_4'][0]
        elif '"sic_code_ids_5":' in RAW:
            englishmessage = temp['API Push Failed']['sic_code_ids_5'][0]
        elif '"operating_hours":' in RAW:
            englishmessage = temp['API Push Failed']['operating_hours'][0]    
        elif '"name":' in RAW:
            englishmessage = temp['API Push Failed']['name'][0]   
        elif '"company_description":' in RAW:
            englishmessage = temp['API Push Failed']['company_description'][0]   
        elif '"professional_last_name":' in RAW:
            englishmessage = temp['API Push Failed']['professional_last_name'][0]
        elif '"website":' in RAW:
            englishmessage = temp['API Push Failed']['website'][0]
        elif '"professional_email":' in RAW:
            englishmessage = temp['API Push Failed']['professional_email'][0]
        elif '"categories":' in RAW:
            englishmessage = temp['API Push Failed']['categories']
        elif '"phone":' in RAW:
            englishmessage = temp['API Push Failed']['phone'][0]
        elif '"loc_bizcontact":' in RAW:
            englishmessage = temp['API Push Failed']['loc_bizcontact']
        else:
            englishmessage = temp['API Push Failed']
            team = 'SRE'
        
        #print(englishmessage)
        
    return [englishmessage,team]

############################################################################################################
#Returns a formatted version of the RAW N49 error
############################################################################################################
def formatn49error(error, englishmessage):

    if 'Failed to get listing_state' in error:
        englishmessage = 'Failed to get listing_state'
        team = 'SRE'
    
    elif 'Unexpected error occurred.' in error:
        englishmessage = 'Unexpected error occurred.'
        team = 'SRE'
        
    elif 'Too Many Requests' in error:
        englishmessage = 'Too Many Requests'
        team = 'SRE'
        
    elif '"statusCode":409' in error:
        englishmessage = 'statusCode:409'
        team = 'SRE'
        
    elif 'Endpoint request timed out' in error:
        englishmessage = 'Endpoint request timed out'
        team = 'SRE'
        
    elif 'listing_status' in error:
        englishmessage = 'Application Error'
        team = 'SRE'
    
    elif 'ECONNRESET' in error:
        englishmessage = 'TCP Connection reset'
        team = 'SRE'
        
    else:
        
        team = 'OPS'
        
        RAW = str(error).replace('"', '')
        RAW = RAW.replace("'",'"').replace('"{','{').replace('}"','}')
        RAW = RAW.replace(' err:',' "err":').replace('message:','"message":').replace(' error:',' "error":').replace('error_description:','"error_description":')
        RAW = RAW.replace('field:','"field":').replace('content:','"content":').replace(' description:','"description":')
        RAW = RAW.replace(' status:','"status":').replace('listing_status:','"listing_status":')
        RAW = RAW.replace('\\"','"').replace('\\\\"',"'")
        RAW = RAW.replace('\\','/').replace('///','')
       
        print(RAW)
        temp = json.loads(RAW)
        print(temp)
        
        if '"err":' in RAW:
            englishmessage = temp['API Push Failed']['err']
        elif '"error_description":' in RAW:
            englishmessage = temp['API Push Failed']['error']['error_description']
        elif '"description":' in RAW and '"field":' in RAW:
            englishmessage = temp['API Push Failed']['error'][0]['description']
        elif '"status":' in RAW:
            englishmessage = temp['API Push Failed']['description']
        elif '"description":' in RAW and '"field":' not in RAW:
            englishmessage = temp['API Push Failed']['error']['description']
        elif '"message":' in RAW:
            englishmessage = temp['API Push Failed']['message']
        else:
            englishmessage = temp['API Push Failed']
            team = 'SRE'
        
        #print(englishmessage)
        
    return [englishmessage,team]

############################################################################################################
#Returns a formatted version of the RAW Bing error
############################################################################################################
def formatbingerror(error, englishmessage):

    if 'Failed to get listing_state' in error:
        englishmessage = 'Failed to get listing_state'
        team = 'SRE'
    
    elif 'Unexpected error occurred.' in error:
        englishmessage = 'Unexpected error occurred.'
        team = 'SRE'
    
    elif 'Dropped' in error:
        englishmessage = 'Dropped - Resolved within 2 weeks'
        team = 'SRE'
    
    elif '"statusCode":409' in error:
        englishmessage = 'statusCode:409'
        team = 'SRE'
        
    elif 'Provide a new store id and retry to add the business or use UpdateBusiness API to edit the business.' in error:
        englishmessage = 'Provide a new store id and retry to add the business or use UpdateBusiness API to edit the business.'
        team = 'SRE'
        
    elif 'listing_status' in error:
        englishmessage = 'Application Error'
        team = 'SRE'
        
    elif 'ECONNRESET' in error:
        englishmessage = 'TCP Connection reset'
        team = 'SRE'
        
    else:
        
        team = 'OPS'
        
        RAW = str(error).replace('"', '')
        RAW = RAW.replace("can\\\\\\'t", 'cannot')
        RAW = RAW.replace("'\\'", "'").replace("\\''", "'")
        RAW = RAW.replace("'", '"').replace('message:', '"message":').replace('details:', '"details":')
        RAW = RAW.replace('ColumnName:', '"ColumnName":').replace('ErrorMessage:', '"ErrorMessage":').replace('\"[','[').replace(']\"',']')
        RAW = RAW.replace('SubIssueType:', '"SubIssueType":').replace('IssueType:', '"IssueType":').replace('DuplicateStoreIds:', '"DuplicateStoreIds":').replace('Message:', '"Message":')
        RAW = RAW.replace('{ err:', '{ "err":')
        RAW = RAW.replace('\\','').replace('"{','{').replace('}"','}')
        
        print(RAW)
        temp = json.loads(RAW)
        print(temp)
        
        if '"err":' in RAW:
            englishmessage = temp['API Push Failed']['err']
        elif '"Message":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']['Message']
            team = 'SRE'
        elif '"IssueType":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details'][0]['IssueType']
        elif '"ErrorMessage":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details'][0]['ErrorMessage']
        elif '"details":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']
        else:
            englishmessage = temp['API Push Failed']
            team = 'SRE'
        #print(englishmessage)
        
    return [englishmessage,team]
    
############################################################################################################
#Returns a formatted version of the RAW Hotfrog error
############################################################################################################
def formathotfrogerror(error, englishmessage):

    if 'Failed to get listing_state' in error:
        englishmessage = 'Failed to get listing_state'
        team = 'SRE'
        
    elif 'Cloudflare' in error:
        englishmessage = 'Issue with Hotfrog\'s server'
        team = 'SRE'
        
    elif 'Invalid country code' in error:
        englishmessage = 'Invalid country code'
        team = 'OPS'
        
    elif 'LOCATION_DATA_INSUFFICIENT_FOR_API_CALL' in error:
        englishmessage = 'Missing Information'
        team = 'OPS'
        
    elif 'Value is required.' in error:
        englishmessage = 'Missing field'
        team = 'OPS'
        
    elif 'Unexpected error occurred.' in error:
        englishmessage = 'Unexpected error occurred.'
        team = 'SRE'
    
    elif '"statusCode":409' in error:
        englishmessage = 'statusCode:409'
        team = 'SRE'
        
    elif 'Location not found' in error:
        englishmessage = 'Location not found - Working with Hotfrog'
        team = 'SRE'
        
    elif 'Object reference not set to an instance of an object.' in error:
        englishmessage = 'Object reference not set to an instance of an object.'
        team = 'SRE'
        
    elif 'geoCoordinates are required by hotfrog.' in error:
        englishmessage = 'geoCoordinates are required by hotfrog.'
        team = 'SRE'
        
    elif 'listing_status' in error:
        englishmessage = 'Application Error'
        team = 'SRE'    
        
    elif 'is deprecated, and merged into' in error:
        englishmessage = 'Listing deprecated - Reset listing details'
        team = 'SRE'
    
    elif 'ECONNRESET' in error:
        englishmessage = 'TCP Connection reset'
        team = 'SRE'
        
    else:
    
        team = 'OPS'
        
        RAW = str(error)
        RAW = RAW.replace("'\\'", "'").replace("\\''", "'")
        RAW = RAW.replace("\\'", '"').replace("'",'"')
        RAW = RAW.replace("\\'\\'",'""')
        RAW = RAW.replace('message:', '"message":').replace('details:', '"details":').replace('referenceId:', '"referenceId":').replace('{ err:', '{ "err":')
        RAW = RAW.replace('AdapterError: Invalid', '"AdapterError": "Invalid').replace(') name:', ')", "name":')
        RAW = RAW.replace('errorProperty:', '"errorProperty":')
        RAW = RAW.replace('cause:', '"cause":').replace('isOperational:', '"isOperational":').replace(', code:', ', "code":')
        RAW = RAW.replace('[Object]', '"[Object]"')
        RAW = RAW.replace('"/"','/')
        RAW = RAW.replace('"{','{').replace('}"','}')
        
        print(RAW)
        temp = json.loads(RAW)
        print(temp)
        
        
        if '"err":' in RAW and '"message":' in RAW:
            englishmessage = temp['API Push Failed']['err']['message']
        elif '"err":' in RAW:
            englishmessage = temp['API Push Failed']['err']
        elif '"errorProperty":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']['errorProperty']
        elif '"code"' in RAW:
            englishmessage = temp['API Push Failed'][0]['code']
        elif '"message":' in RAW:
            try:
                englishmessage = temp['API Push Failed'][0]['details']['message']
            except:
                englishmessage = temp['API Push Failed'][0]['details']
        else:
            englishmessage = temp['API Push Failed']
            team = 'SRE'
        
        #print(englishmessage)
        
    return [englishmessage,team]
    
############################################################################################################
#Returns a formatted version of the RAW Showmelocal error
############################################################################################################
def formatshowmelocalerror(error, englishmessage):

    if 'Failed to get listing_state' in error:
        englishmessage = 'Failed to get listing_state'
        team = 'SRE'
        
    elif 'Unexpected error occurred.' in error:
        englishmessage = 'Unexpected error occurred.'
        team = 'SRE'
        
    elif "Cannot read property \\'raw_body\\'" in error:
        englishmessage = 'USR-1230'
        team = 'SRE'
        
    elif 'XML Parsing Error' in error:
        englishmessage = 'XML Parsing Error'
        team = 'SRE'
        
    elif 'A .NET Framework error occurred' in error:
        englishmessage = 'A .NET Framework error occurred'
        team = 'SRE'
        
    elif '"statusCode":409' in error:
        englishmessage = 'statusCode:409'
        team = 'SRE'
    
    elif 'XML parsing' in error:
        englishmessage = 'XML parsing'
        team = 'SRE'
    
    elif 'Insufficient Showmelocal search parameters' in error:
        englishmessage = 'Invalid location name/state/city/country or phone'
        team = 'OPS'
        
    elif 'listing_status' in error:
        englishmessage = 'Application Error'
        team = 'SRE'
        
    elif 'ECONNRESET' in error:
        englishmessage = 'TCP Connection reset'
        team = 'SRE'
    
    else:
        
        team = 'OPS'
        
        RAW = str(error)
        RAW = RAW.replace("\\\\\\'","'")
        RAW = RAW.replace("'\\'","'").replace("\\''","'")
        RAW = RAW.replace("\\'","'")
        RAW = RAW.replace("'",'"')
        RAW = RAW.replace('message:', '"message":').replace('details:', '"details":').replace('result:','"result":').replace(' status:','"status":').replace('conflict:','"conflict":').replace('{ err:','{ "err":')
        RAW = RAW.replace('error_number:','"error_number":').replace('error_description:','"error_description":').replace('error_source:','"error_source":').replace(' error:',' "error":')
        RAW = RAW.replace('listing_status:','"listing_status":').replace('raw_body:','"raw_body":')
        RAW = RAW.replace('"{','{').replace('}"','}').replace('"/"','/')
        
        print(RAW)
        temp = json.loads(RAW)
        print(temp)
        
        if '"err":' in RAW:
            englishmessage = temp['API Push Failed']['err']
        elif '"error_description":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']['error_description']
        elif '"listing_status":' in RAW:
            englishmessage = temp['API Push Failed']['error'][0]['details']
            team = 'SRE'
        elif '"conflict":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']['result']['conflict']
        elif '"message":' in RAW:
            englishmessage = temp['API Push Failed'][0]['details']
        else:
            englishmessage = temp['API Push Failed']
            team = 'SRE'

        #print(englishmessage)
        
    return [englishmessage,team]
    
if __name__ == '__main__': main()