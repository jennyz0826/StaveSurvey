#!/bin/env python
import os, sys
import argparse

import dbAccess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add attachment to component in production database")
    parser.add_argument("--code", help="DB code of component")
    parser.add_argument("--title", help="Short description")
    parser.add_argument("--message", "-m", dest="message", help="Comment about attachment")
    parser.add_argument("--file", help="File to attach")
    parser.add_argument("--file-name-override", help="Override file-name of attachment")
    parser.add_argument("--test", action="store_true", help="Don't write to DB")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    import dbAccess

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    if not args.code:
        print("Need code of component, try 'read_db.py list_components'")
        sys.exit(1)

    if not args.file:
        print("Need name of file to attach")
        sys.exit(1)

    if not args.title:
        print("Need short message")
        sys.exit(1)

    if not args.message:
        print("Don't have a long message")
        sys.exit(1)

    print("Add attachment to component:")
    print("    Component code: %s" % args.code)
    print("    Short: %s" % args.title)
    if args.file_name_override:
        print("    File-name: %s (known as %s)" % (args.file, args.file_name_override))
    else:
        print("    File-name: %s" % args.file)

    print("    Message: %s" % args.message)

    if args.test:
        print("Exit early for testing")
        sys.exit(1)

    try:
        data = {}
        data["component"] = args.code
        data["title"] = args.title
        data["description"] = args.message

        if args.file_name_override:
            attachment = {"data": (args.file_name_override, open(args.file, 'rb'))}
        else:
            attachment = {"data": open(args.file, 'rb')}
        result = dbAccess.doSomething("createComponentAttachment",
                                      data, attachments = attachment)
        # Responds with...

        print(result)
    except Exception as e:
        if args.verbose:
            print("Request failed:")
            import traceback
            traceback.print_exc()
        else:
            print("Request failed, use --verbose flag for more information")
