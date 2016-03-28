import sublime, sublime_plugin, json

def plugin_loaded():
    # Convert the main menu in an Array
    global mainMenu
    mainMenu = parseFile('MainMenu.json')

# This function reads a JSON file in package folder and returns an Array
def parseFile(file):
    fileContents = sublime.load_resource("/".join(["Packages", __package__, file]))
    jsonObj = json.loads(fileContents)
    return jsonObj

# Returns the 'name' and 'memo' fileds from a menu array to be used as menu options
def getMenuItems(optionsArray, includeMemo):
    menuItems = []
    if includeMemo:
        for item in optionsArray:
            menuItem = [item['name'], item['memo']]
            menuItems.append(menuItem)
    else:
        menuItems = [[item['name']] for item in optionsArray];
    return menuItems

class NsMenuCommand(sublime_plugin.TextCommand):
    # Show Main Menu or depending on the text selected, go directly to the submenu
    def run(self, edit):
        # if the text selected is the same as the submeny keyword, go directly to the submenu
        currentSelection = self.view.substr(self.view.sel()[0])
        if currentSelection:
            for submenu in mainMenu:
                if submenu['keyword'] == currentSelection:
                    self.showSubmenu(mainMenu.index(submenu))
                    break
        self.showMainMenu();

    def showSubmenu(self, menuId):
        if menuId==-1:
            return
        # Get the default action from the Main Menu file
        action = mainMenu[menuId]['defaultAction']
        # Get the file where the submenu is defined
        fileName = mainMenu[menuId]['internalid']
        # Check if the memo field needs to be included in the submenu options
        showMemo = mainMenu[menuId]['showMemo']
        # Convert the submenu file in an Array
        submenuArray = parseFile(fileName)
        # Show the submenu
        self.view.window().show_quick_panel(getMenuItems(submenuArray, showMemo), lambda id: self.executeAction(id, action, submenuArray))

    # execute the menu action
    def executeAction(self, id, action, optionsArray):
        if id==-1:
            return
        #override the default action, if any
        try :
            if optionsArray[id]['action']:
                action = optionsArray[id]['action']
        except:
            pass
        # Execute the menu option action
        print(action)
        if action=='insertInternalId':
            self.insertInternalId(id, optionsArray)
        if action=='insertSnippet':
            self.insertSnippet(id, optionsArray)
        if action=='showMainMenu':
            self.showMainMenu()
        if action=='uploadFile':
            self.uploadFile()
        if action=='openProjectSettingsFile':
            self.openProjectSettingsFile()
        if action=='openIntegrationHelp':
            self.openIntegrationHelp()

    # Menu Actions:

    def insertInternalId(self, id, optionsArray):
        internalid = optionsArray[id]['internalid'];
        self.view.run_command("insert", {"characters": internalid})

    def insertSnippet(self, id, optionsArray):
        self.view.run_command("insert_snippet", {"name": "/".join(["Packages", __package__, "Template Files", optionsArray[id]['internalid']]) })

    def showMainMenu(self):
        self.view.window().show_quick_panel(getMenuItems(mainMenu, False), self.showSubmenu)

    def uploadFile(self):
        self.view.run_command("ns_upload_script")

    def openProjectSettingsFile(self):
        self.view.window().run_command("ns_open_project_settings")

    def openIntegrationHelp(self):
        self.view.window().run_command('new_file')
        view = self.view.window().active_view()
        view.run_command("insert_snippet", {"name": "/".join(["Packages", __package__, "Integration Help.sublime-snippet"]) })
        view.set_name('Integration Help.txt')

