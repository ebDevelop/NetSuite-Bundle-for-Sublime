import sublime, sublime_plugin, json

mainMenu = ['Record Type IDs', 'Templates', 'Sublist IDs']

def plugin_loaded():
    # Load Record Type IDs
    global recordTypeOptions, recordTypes
    recordTypeOptions = []
    recordTypesJsonString = sublime.load_resource("/".join(["Packages", __package__, "RecordTypes.json"]))
    recordTypes = json.loads(recordTypesJsonString)
    recordTypeOptions = [[record['name']] for record in recordTypes];

    # Load Template Library
    global templates, templateOptions
    templateJsonString = sublime.load_resource("/".join(["Packages", __package__, "Templates.json"]))
    templates = json.loads(templateJsonString)
    templateOptions = []
    for record in templates:
        menuItem = [record['name'], record['description']]
        templateOptions.append(menuItem)

    # Load Sublist IDs
    global sublistOptions, sublists
    sublistOptions = []
    sublistOptionsJsonString = sublime.load_resource("/".join(["Packages", __package__, "SublistIDs.json"]))
    sublists = json.loads(sublistOptionsJsonString)
    for sublist in sublists:
        menuItem = [sublist['name'], sublist['location']]
        sublistOptions.append(menuItem)

class NetsuiteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        currentSelection = self.view.substr(self.view.sel()[0])
        if currentSelection== 'type':
            self.showSubmenu(0)
        if currentSelection== 'sublist':
            self.showSubmenu(2)
        else:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)

    def showSubmenu(self, id):
        # Record Type IDs
        if id==0:
            self.view.window().show_quick_panel(recordTypeOptions, self.insertRecordTypeId)
        # Templates
        if id==1:
            self.view.window().show_quick_panel(templateOptions, self.insertSnippet)
        if id==2:
            self.view.window().show_quick_panel(sublistOptions, self.insertSublistId)

    def insertRecordTypeId(self, id):
        # Back
        if id==0:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)
        # A Record Type was selected
        if id>0:
            recordid = recordTypes[id]['internalid'];
            self.view.run_command("insert", {"characters": recordid})

    def insertSnippet(self, id):
        # Back
        if id==0:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)
        # A Template was selected
        if id>0:
            #insert snippet
            self.view.run_command("insert_snippet", {"name": "/".join(["Packages", __package__, "Template Files", templates[id]['file']]) })

    def insertSublistId(self, id):
        # Back
        if id==0:
            self.view.window().show_quick_panel(mainMenu, self.showSubmenu)
        # A Record Type was selected
        if id>0:
            sublistId = sublists[id]['internalid'];
            self.view.run_command("insert", {"characters": sublistId})
