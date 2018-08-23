#!/bin/env python
import dbAccess

if __name__ == "__main__":
    token = dbAccess.authenticate()
    print("export ITK_DB_AUTH=%s" % token)

