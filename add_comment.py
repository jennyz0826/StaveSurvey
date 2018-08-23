#!/bin/env python
import os, sys
import argparse

import dbAccess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add comment to component in production database")
    parser.add_argument("--code", help="DB code of component")
    parser.add_argument("--component-type", help="Component type to list")
    parser.add_argument("--message", "-m", dest="message", help="Comment to apply")
    parser.add_argument("--test", action="store_true", help="Don't write to DB")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

#    print("Command: %s" % args.command)

    import dbAccess

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    if args.code:
        print("Have code to refer to component %s" % args.code)
        if args.component_type:
            print("Don't need component type as well as code");
            sys.exit(1)
    else:
        if args.component_type:
            print("Should now list components of type %s" % args.component_type)

            # Can also filter by "subproject", "type", "currentStage"
            c_list = dbAccess.extractList("listComponents", method = "GET",
                                          data = {"project": "S",
                                                  "componentType": args.component_type},
                                          output = "code")

            # Other outputs: "currentState", "type", "subproject"

            for c in c_list:
                print("   %s" % c)

            sys.exit(1)
        else:
            print("Need component code, or components type")
            print("  Known component codes (in strips):")

            c_list = dbAccess.extractList("listComponentTypes", method = "GET",
                                          data = {"project": "S"},
                                          output = ["code", "name"])

            for c, n in c_list:
                print("    %s: %s" % (c, n))

                #dbAccess.printGetList("listComponentTypes", method = "GET",
                #                  data = {"project":"S"})

            sys.exit(1)

    if not args.message:
        print("Don't have a message")
        sys.exit(1)

    print("Add comment to component:")
    print("    Component code: %s" % args.code)
    print("    Message: %s" % args.message)

    if args.test:
        sys.exit(1)

    try:
        result = dbAccess.doSomething("createComponentComment",
                                      {"component": args.code, 
                                       "comments": [args.message]})
        # Responds with information about transaction
        # {u'uuAppErrorMap': {},
        #  u'component': {u'componentType': u'59d608c6ed67730005160cd6',
        #                 u'tests': [], u'code': u'469123d57abd3579de7a92cb0116e753',
        #                 u'attachments': [], u'serialNumber': u'20USEH00000002',
        #                 u'stages':
        #                     [{u'code': u'BARE', u'dateTime': u'2017-12-30T21:21:31+01:00'}],
        #                 u'comments':
        #                     [{u'comment': u'Text of comment', u'userIdentity': u'19-7000-1', u'code': u'708b776aa0c22ef7cb1df16d', u'dateTime': u'2018-01-22T15:32:23+01:00'}],
        #                 u'institution': u'59d60ee4ed67730005160cd9',
        #                 u'project': u'S', u'state': u'requestedToDelete',
        #                 u'userIdentity': u'6-11-1',
        #                 u'sys': {u'mts': u'2018-01-22T14:32:23.001Z', u'rev': 2, u'cts': u'2017-12-30T20:21:31.635Z'}, u'currentStage': u'BARE', u'subproject': u'SE', u'type': u'R0H0', u'id': u'5a47f54bb34fe10'....

        print(result)
    except:
        if args.verbose:
            print("Request failed:")
            import traceback
            traceback.print_exc()
        else:
            print("Request failed, use --verbose flag for more information")
