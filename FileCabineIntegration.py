import sublime, sublime_plugin, urllib, os, json, base64, os.path
import xml.etree.ElementTree as ET

global URL 

def loadResource(name):
    fileContent = sublime.load_resource("/".join(["Packages", __package__, name]))
    return fileContent

def setUrl(folderSettings):
    global URL
    URL = folderSettings['url'] + '/services/NetSuitePort_2015_1'

# finds the NetSuite internal ID of the folder specified in the Project Seetings file
def getProjectFolderId(folderName, projectSettings):
    soapRequest = loadResource('searchProjectFolder') % projectSettings
    soapRequest = soapRequest.format(folder_name=folderName)
    soapRequest =  str.encode(soapRequest)
    resp = makeRequest('search', soapRequest)
    resp = ET.fromstring(resp)
    status = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}status').attrib['isSuccess']
    if status == 'true':
        totalRecords = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}totalRecords').text
        if totalRecords == '1':
            return resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}recordList')[0].attrib['internalId']
        elif totalRecords == '0':
            raise ValueError('The folder specificed in the Project Settings file ['+ folderName + '] does not exist in the file Cabinet\nCreate the folder in the file cabinet and try again') 
        else:
            raise ValueError('There are '+ totalRecords +' folders with the same name of the folder specificed in the Project Settings file ['+ folderName + '] \nThe folder name needs to be unique') 

# walk through to directoy tree [from the folder where the Project Settins file is located to the the folder when the file that will be uploaded is located]
# checking if the folder exists in NetSuite.
def getSubfolderId(filePath, localRootFolder, NetsuiteProjectFolderId, projectSettings):
    folders = filePath[(len(localRootFolder.replace('/','\\'))):]
    folders = localRootFolder[localRootFolder.rfind('/')+1:] + folders
    folders = folders.split('\\')
    folderId = None
    parentFolder = NetsuiteProjectFolderId
    for folder in folders:
       print(folder)
       folderId = getFolder(folder, parentFolder, projectSettings);
       parentFolder = folderId
    return folderId

# search for a folder with parent folders in NetSuite
# if the folder exists, return the internal Id
# if the folder doen't exists, create it and return the internal ID
def getFolder(folderName, parentFolder, projectSettings):
    soapRequest = loadResource('searchSubFolder') % projectSettings
    soapRequest = soapRequest.format(folder_name=folderName, parent_folder = parentFolder)
    soapRequest =  str.encode(soapRequest)
    resp = makeRequest('search', soapRequest)
    resp = ET.fromstring(resp)
    status = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}status').attrib['isSuccess']
    if status == 'true':
        totalRecords = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}totalRecords').text
        if totalRecords == '1':
            return resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}recordList')[0].attrib['internalId']
        else:
            return createFolder(folderName, parentFolder, projectSettings)

# create a sub folder in NetSuite
def createFolder (folderName, parentFolder, projectSettings): 
    soapRequest = loadResource('addFolder') % projectSettings
    soapRequest = soapRequest.format(folder_name=folderName, parent_folder = parentFolder)
    soapRequest =  str.encode(soapRequest)
    resp = makeRequest('add', soapRequest)
    resp = ET.fromstring(resp)
    status = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}status').attrib['isSuccess']
    folderId = 0
    print('status: ' + status)
    if status == 'true':
        folderId = resp.find('.//{urn:messages_2015_1.platform.webservices.netsuite.com}baseRef').attrib['internalId']
    return folderId

def makeRequest(action, postData):
    headers = {'SOAPAction': action, 'Content-Type': 'application/xml',}
    req = urllib.request.Request(URL, postData, headers)
    with urllib.request.urlopen(req) as response:
       return response.read()

# finds the Project Seetings file in the directory tree starting from the folder
# passed as parameter
def findProjectSettings(folder):
    found = 0
    limit = 0

    if folder is None:
        return None
    
    start_path    = folder
    last_root    = 'C:'
    current_root = start_path
    
    while limit < 20 and current_root != last_root:
        if os.path.isfile(current_root + '/ProjectSettings.json'):
            found = 1
            break
        current_root = current_root[:-(len(current_root)-current_root.rfind('\\'))]
        limit = limit+1

    current_root = current_root.replace('\\', '/');
    current_root = current_root.replace('C:', '/C');

    if found == 1:
        return "/".join([current_root, "ProjectSettings.json"])
    else:
        raise ValueError('The Project Settings file was not found in the directoy tree.\nPlease go to Ctrl+Alt+n > Integration > Project Settings to create a Project File.')

# Updaload the active file to the file cabinet
class NsUploadScriptCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            # get the file path
            try:
                folder = os.path.dirname(self.view.file_name())
            except:
                raise ValueError('Please save the file first before uploading it to the File Cabinet') 


            # find the Project settings folder
            projectSettings = findProjectSettings(folder)

            # Project Settings folder path (project root folder)
            projectSettingsFolder = projectSettings[:-(len(projectSettings)-projectSettings.rfind('/'))]

            # convert the project seeting file into a JSON array
            projectSettings = projectSettings.replace('/C', 'C:');
            projectSettings = projectSettings.replace('/', '\\');
            projectSettings = open(projectSettings, 'r')
            jsonContent = json.loads(projectSettings.read())
            projectSettings.close()

            # set the web services URL based on the project settings
            setUrl(jsonContent)

            # get the file cabine folder ID of the folder selected in the project settings file
            # the projectSettingsFolder will be created under this folder 
            projectFolderId = getProjectFolderId(jsonContent['folder'], jsonContent)

            # Get the Id of final folder where the file will be created
            # This function creates the folder directory in the file cabinet (under the projectFolderId folder)
            # if the folders doen't exisit
            folderId = getSubfolderId(folder, projectSettingsFolder, projectFolderId, jsonContent)

            #upload the file to the file cabinet:

            soapRequest = loadResource('addFile') % jsonContent

            pos = self.view.sel()[0]
            self.view.run_command('select_all')
            contents = self.view.substr(self.view.sel()[0])
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(pos.a, pos.b))

            
            contents = str.encode(contents)
            contents = base64.b64encode(contents)
            contents = contents.decode('unicode_escape')

            file_name = os.path.basename(self.view.file_name())

            soapRequest = soapRequest.format(contents=contents, file_name=file_name, folder_id=folderId)
            soapRequest = str.encode(soapRequest)
            resp = ET.fromstring(makeRequest('add', soapRequest))

            isSuccess = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}status').attrib['isSuccess']

            if isSuccess == 'true':
                sublime.status_message('File ' + file_name + ' uploaded successfully to account ' + jsonContent['account'])
            else:
                error = resp.find('.//{urn:core_2015_1.platform.webservices.netsuite.com}message').text
                error = 'File upload failed: ' + error
                sublime.message_dialog(error)
                
        except urllib.error.HTTPError as e:
            error = e.read()
            error = ET.fromstring(error)
            error = 'File upload failed: ' +  error.find('.//faultstring').text
            sublime.message_dialog(error)
        except ValueError as error:
            sublime.message_dialog(str(error))

#Finds and open the NetSuite Project Seetings JSON file 
class NsOpenProjectSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        found = 0
        limit = 0

        folder = None
        projectSettings = None
        try:
            folder = os.path.dirname(view.file_name())
            projectSettings = findProjectSettings(folder)
        except:
            folder = None
            projectSettings = None

        if projectSettings:
            self.window.run_command('open_file', {"file": projectSettings})
        else:
            self.window.run_command('new_file')
            view = self.window.active_view()
            view.run_command("insert_snippet", {"name": "/".join(["Packages", __package__,"ProjectSettings.sublime-snippet"]) })
            view.set_name('ProjectSettings.json')


class NsOpenIntegrationHelpCommand(sublime_plugin.WindowCommand):
    def run(self):
        print('entered')
        self.window.run_command('open_file', {"file": "/".join(["Packages", __package__, 'Integration Help.txt'] )})
