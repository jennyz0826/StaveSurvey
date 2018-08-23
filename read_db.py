#!/bin/env python
import os, sys
import argparse

import dbAccess

def list_commands():
    print("Available commands:")
    c = list(commands.keys())
    c.sort()
    print("\t"+("\n\t".join(c)))

def list_component_type_codes(**kwargs):
    project = kwargs["project"]

    c_list = dbAccess.extractList("listComponentTypes", method = "GET",
                                  data = {"project": project},
                                  output = ["code", "name"])

    for c, n in c_list:
        print("    %s: %s" % (c, n))

class FunctionCommand(object):
    def __init__(self, *args):
        self.function = args[0]
        self.allowed = args[1]
        self.required = self.allowed

    def run(self, **kwargs):
        self.function(**kwargs)

class StandardCommand(object):
    def __init__(self, *args):
        # type(args) is tuple
        self.action = args[0]
        self.allowed = args[1]
        self.required = list(self.allowed)
        if len(args) > 2:
            for o in args[2]:
                self.required.remove(o)

    def run(self, **kwargs):
        actionData = kwargs

        try:
            dbAccess.printGetList(self.action,
                                  method = "GET",
                                  data = actionData)
        except:
            if dbAccess.verbose:
                print("Request failed:")
                import traceback
                traceback.print_exc()
            else:
                print("Request failed, use --verbose flag for more information")

SC = StandardCommand
FC = FunctionCommand
commands = {"stats": SC("getItkpdOverallStatistics", []),
            "list_institutes": SC("listInstitutions", []),
            "list_component_types": SC("listComponentTypes", ["project"]),
            "list_component_type_codes": FC(list_component_type_codes,
                                            ["project"]),
            "list_components": SC("listComponents", ["project", "componentType"],
                                  ["componentType"]),
            "list_all_attachments": SC("uu-app-binarystore/listBinaries", []),
            "list_projects": SC("listProjects", []),
            "list_test_types": SC("listTestTypes", ["project", "componentType"]),
            "list_commands": FC(list_commands, []),
            "get_component_info": SC("getComponent", ["component"]),
            "summary": FC(dbAccess.summary, ["project"])
            }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read from production database")
    parser.add_argument("command", help="What to do (list_commands for help)")
    parser.add_argument("--component-type", help="Code for the type of component to query")
    parser.add_argument("--component-id", help="Either code, or SN for the component in question")
    parser.add_argument("--project", help="Code for the project, defaults to 'S' for Strips")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    print("Command: %s" % args.command)

    import dbAccess

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    if args.command not in commands:
        list_commands()
        sys.exit(0)

    extraData = {}
    if args.component_type is not None:
        extraData["componentType"] = args.component_type

    if args.component_id is not None:
        extraData["component"] = args.component_id

    if args.project is not None:
        extraData["project"] = args.project

    data = commands[args.command]

    if "project" in data.allowed and "project" not in extraData:
        extraData["project"] = "S"

    for k in extraData.keys():
        if k not in data.allowed:
            print("Arg for %s not allowed for command %s" % (k, args.command))
            print(" need (%s)" % ', '.join(data.allowed))
            sys.exit(1)

    for k in data.required:
        if k not in extraData.keys():
            print("Arg for %s is required for command %s" % (k, args.command))
            print(" need (%s)" % ', '.join(data.required))
            sys.exit(1)

    data.run(**extraData)
