import sublime, sublime_plugin, json

mainMenu = ['Record Type IDs', 'Templates', 'Sublist IDs']

def plugin_loaded():
    # Convert Files to Arrays
    global recordTypeIds, sublistIds, templates
    recordTypeIds = parseFile('RecordTypes.json')
    sublistIds = parseFile('SublistIDs.json')
    templates = parseFile('Templates.json')

def parseFile(file):
    fileContents = sublime.load_resource("/".join(["Packages", __package__, file]))
    jsonObj = json.loads(fileContents)
    return jsonObj

def getMenuItems(optionsArray, includeMemo):
    menuItems = []
    if includeMemo:
        for item in optionsArray:
            menuItem = [item['name'], item['memo']]
            menuItems.append(menuItem)
    else:
        menuItems = [[item['name']] for item in optionsArray];
    return menuItems

class NetsuiteCommand(sublime_plugin.TextCommand):
    # Show Main Menu. Depending on the text selected, go directly to the submenu
    def run(self, edit):
        currentSelection = self.view.substr(self.view.sel()[0])
        if currentSelection== 'type':
            self.showSubmenu(0)
        if currentSelection== 'sublist':
            self.showSubmenu(2)
        else:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)

    def showSubmenu(self, menuId):
        # Record Type IDs
        if menuId==0:
            self.view.window().show_quick_panel(getMenuItems(recordTypeIds, True), lambda id: self.insertInternalId(id, recordTypeIds))
        # Templates
        if menuId==1:
            self.view.window().show_quick_panel(getMenuItems(templates, True), self.insertSnippet)
        #sublist IDs
        if menuId==2:
            self.view.window().show_quick_panel(getMenuItems(sublistIds, True), lambda id: self.insertInternalId(id, sublistIds))

    def insertInternalId(self, id, optionsArray):
        # Back
        if id==0:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)
        # A menu item was selected
        if id>0:
            internalid = optionsArray[id]['internalid'];
            self.view.run_command("insert", {"characters": internalid})

    def insertSnippet(self, id):
        # Back
        if id==0:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)
        # A Template was selected
        if id>0:
            #insert snippet
            self.view.run_command("insert_snippet", {"name": "/".join(["Packages", __package__, "Template Files", templates[id]['internalid']]) })
