#!/bin/env python3

import sys

try:
    # Installed by default on lxplus
    import requests
except:
    print("Please install the requests module,")
    print("the equivalent of one of the following:")
    print("  pip install requests")
    print("  yum install python-requests")
    sys.exit(1)

import json

verbose = False

token = None

import os
testing = False
if os.getenv("TEST_OVERRIDE"):
    testing = True

def setupConnection():
    global token

    print("Setup connection")

    token = authenticate()

def to_bytes(s):
    try:
        return bytes(s, 'utf-8')
    except TypeError:
        # Python 2, already OK
        return s

# DB has unicode, but console might be something else
# If eg ASCII, replace unicode chars
# If directed to file, force utf-8
def fix_encoding(s):
    enc = sys.stdout.encoding

    # Default to utf-8 if redirected
    if enc is None:
        enc = "utf-8"

    if sys.version_info[0] == 2:
        return s.encode(enc, "replace")
    else:
        # Encode string into bytes
        s = s.encode(enc, "replace")
        s = s.decode(enc, "replace")
    return s

def authenticate(accessCode1 = None, accessCode2 = None):
    print("Getting token")
    # post
    # Everything is json header

    a = {"grant_type": "password"}

    if accessCode1 is not None and accessCode2 is not None:
        a["accessCode1"] = accessCode1
        a["accessCode2"] = accessCode2
    else:
        import getpass

        a["accessCode1"] = getpass.getpass("AccessCode1: ")
        a["accessCode2"] = getpass.getpass("AccessCode2: ")

    a = to_bytes(json.dumps(a))

    print("Sending credentials to get a token")

    result = doSomething("grantToken", a,
                         url = "https://oidc.plus4u.net/uu-oidcg01-main/0-0/")

    # print("Authenticate result:", result)

    j = to_bytes(result)
    id_token = j["id_token"]

    return id_token

def listComponentTypes():
    printGetList("listComponentTypes?project=S",
                 output = "{name} ({code})")

def doMultiSomething(url, paramdata = None, method = None,
                     headers = None,
                     attachments = None):

    if verbose:
        print("Multi-part request to %s" % url)
        print("Send data: %s" % paramdata)
        print("Send headers: %s" % headers)
        print("method: POST")

    # print paramdata
    r = requests.post(url, data = paramdata, headers = headers,
                      files = attachments)

    if r.status_code in [500, 401]:
        print("Presumed auth failure")
        print(r.json())
        return None

    if r.status_code != 200:
        print(r)
        print(r.status_code)
        print(r.headers)
        print(r.text)
        r.raise_for_status()

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

# Passed the uuAppErrorMap part of the message response
def decodeError(message, code):
    if "uu-app-server/internalServerError" in message:
        # Eg authentication problem "Signature verification raised"
        message = message["uu-app-server/internalServerError"]
        message = message["message"]
        print("Server responded with error message (code %d):"
              % code)
        print("\t%s" % message)
        return

    found = False

    for k in message.keys():
        if "cern-itkpd-main" in k:
            if "componentTypeDaoGetByCodeFailed" in k:
                found = True
                print("Either component type is invalid, or nothing found")
                continue
            elif "invalidDtoIn" in k:
                print("Decoding error message in %s" % k)
                found = True
        else:
            continue

        info = message[k]

        if "paramMap" in info:
            paramInfo = info["paramMap"]
            if "missingKeyMap" in paramInfo:
                for (k, v) in paramInfo["missingKeyMap"].items():
                    if len(v.keys()) == 1:
                        reason = v[v.keys()[0]]
                    else:
                        print(v.keys())
                        reason = v

                    if "$" in k:
                        # Seem to have $. in front
                        param_name = k[2:]
                    else:
                        param_name = k
                    print("Key '%s' missing: %s" % (param_name, reason))
            # There's probably also a invalidValueKeyMap which might be useful
        else:
            print(info)

    if not found:
        print("Unknown message: %s" % message)

def doRequest(url, data = None, headers = None, method = None):
    if method == "post" or method == "POST" or (method is None and data is not None):
        method = "POST"
    else:
        method = "GET"

    if verbose:
        print("Request to %s" % url)
        print("Send data %s" % data)
        print("Send headers %s" % headers)
        print("method %s" % method)

    if method == "POST":
        # print("Sending post")
        r = requests.post(url, data = data,
                          headers = headers)
    else:
        # print("Sending get")
        r = requests.get(url, data = data,
                         headers = headers)

    if r.status_code == 401:
        j = r.json()
        if "uuAppErrorMap" in j and len(j["uuAppErrorMap"]) > 0:
            if "uu-oidc/invalidToken" in j["uuAppErrorMap"]:
                global token
                print("Auth failure, need a new token!")
                token = None
                raise Exception("Auth failure, token out of date")

    if r.status_code != 200:
        try:
            message = r.json()["uuAppErrorMap"]

            if verbose:
                print(r.status_code)
                print(r.headers)
                print("errormap: %s" % message)
            decodeError(message, r.status_code)
            raise BaseException("Error")
        except Exception as a:
            print("Failed to decode error: %s" % a)
            # print(r)
            print(r.status_code)
            print(r.headers)
            print(r.text)
            raise BaseException("Bad status code")

    if "content-type" in r.headers:
        # Expect "application/json; charset=UTF-8"
        ct = r.headers["content-type"]
        if ct.split("; ")[0] != "application/json":
            print("Received unexpected content type: %s" % ct)
    else:
        print(r.headers)

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

def doSomething(action, data = None, url = None, method = None,
                attachments = None):
    if testing:
        return doSomethingTesting(action, data, url, method, attachments)

    if token is None and url is None:
        setupConnection()
        if token is None:
            print("Authenticate failed")
            return

    # baseName = "https://plus4u.net...."
    if url is None:
        baseName = "https://uuappg01.plus4u.net/cern-itkpd-test/"
        baseName += "98234766872260181-dcb3f6d1f130482581ba1e7bbe34413c/"
    else:
        baseName = url

    baseName += action

    if attachments is not None:
        # No encoding of data, as this is passed as k,v pairs
        headers = {"Authorization": "Bearer %s" % token}
        return doMultiSomething(baseName, paramdata = data,
                                headers = headers,
                                method = method, attachments = attachments)

    if data is not None:
        if type(data) is bytes:
            reqData = data
        else:
            reqData = to_bytes(json.dumps(data))
        if url is None: # Default
            pass # print("data is: ", reqData)
    else:
        reqData = None

    headers = {'Content-Type' : 'application/json'}
    # Header, token
    if token is not None:
        headers["Authorization"] = "Bearer %s" % token

    result = doRequest(baseName, data = reqData,
                       headers = headers, method = method)

    return result

def extractList(*args, **kw):
    "Extract data for a list of things (as json)"
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]

    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        print("Response not json: %s" % data)
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:
            print(j)
            return
    else:
        # Sublist
        l = j["pageItemList"]

    if output is None:
        # All data
        return l
    else:
        # Just one piece
        if type(output) is list:
            result = []
            for i in l:
                result.append(list(i[o] for o in output))
            return result
        else:
            return [i[output] for i in l]

def printItem(item, format):
    print(format.format(**item))

def printGetList(*args, **kw):
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]
    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        print("Response not json: %s" % data)
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:

            if isinstance(j,list):
                print(j)
                return
            else:
                l=[j] ##major change here~ So it's gonna go throu printList-->organize things much better
                     ##because from getcomponent, j is not a list
    else:
        # Returned sublist
        l = j["pageItemList"]

    if verbose:
        print(fix_encoding("%s" % l))

    if output is not None:
        for i in l:
            printItem(i, output)
    else:

        printList(l, "print_first" in kw)

# If output is short enough, can print on one line
def isShortDict(d):
    keys = d.keys()

    if "*" in keys: # Threshold bounds
        return True
    if "children" in keys and len(d["children"]) > 0:
        return False
    if "code" in keys and "name" in keys:
        return True
    if "properties" in keys and d["properties"] is not None:
        return False

    return False

simple_type_list = [bool, int, float, str]
if sys.version_info[0] == 2:
    simple_type_list.append(unicode)

def printDict(d, indentation=''):
    # First match common dicts
    keys = list(d.keys())

    if "*" in keys:
        # Threshold: {'*': {'max': None, 'nominal': None, 'min': None}
        print("%s\t*..." % indentation)
        return

    try:
        if "value" in keys:
            # Most things have these parameters
            out = ("%s%s (%s) = %s"
                   % (indentation, d["name"], d["code"], d["value"]))
            out = fix_encoding(out)
            print(out)
            keys.remove("code")
            keys.remove("name")
            keys.remove("value")
        else:
            # Most else have these parameters
            out = ("%s%s (%s)"
                  % (indentation, d["name"], d["code"]))
            out = fix_encoding(out)
            print(out)
            keys.remove("code")
            keys.remove("name")

        # test-type schema
        if "valueType" in keys and d["dataType"] != "compound":
            print("%s  %s %s" % (indentation, d["valueType"], d["dataType"]))
            keys.remove("valueType")
            keys.remove("dataType")
        if "children" in keys:
            keys.remove("children")
            subdict = d["children"]
            if subdict != None:
                printList(subdict, False, indentation)

        if "properties" in keys:
            p = d["properties"]
            if p is None:
                pass
            else:
                # print("%sProperties:" % indentation)
                printList(p, False, indentation)
                keys.remove("properties")

        if "parameters" in keys:
            print("%sParameters:" % indentation)
            printList(d["parameters"], False, indentation)
            keys.remove("parameters")

        if "testTypes" in keys and d["testTypes"] is not None:
            print("%sTest types:" % indentation)
            printList(d["testTypes"], False, indentation)
            keys.remove("testTypes")

        if verbose:
            if len(keys) > 0:
                print("%s\t\t Skipped keys: %s" % (indentation, keys))

        return
    except KeyError:
        # Mostly the lower-level dicts match above patterns
        if len(indentation) > 1:
            print("")
        #    print("%s\tPrint unknown dict (%s)" % (indentation, d.keys()))

    # Generic
    for k, v in d.items():
        if v is None:
            print("%s%s: null" % (indentation, k))
        elif type(v) is str or type(v) is unicode:
            print("%s%s: %s" % (indentation, k,v))
        elif type(v) in [bool, int, float]:
            print("%s%s: %s" % (indentation, k,v))
        elif type(v) is list:
            print("%s%s (%d)" % (indentation, k, len(v)))
            printList(v, False, indentation)
        elif type(v) is dict:
            subdict = v
            # Sometimes short enough for one line
            if isShortDict(v):
                # No-new line difficult with Python 2 and 3
                sys.stdout.write("%s%s:" % (indentation, k))
                printDict(v, " ")
            else:
                print("%s%s:" % (indentation, k))
                printDict(v, indentation+"\t")
        else:
            print("%s?Type: %s: %s" % (indentation, k, v))

def printList(l, print_first, indentation='', location=''):
    first = True

    startLine = indentation + "\t"

    for i in l:
        if len(indentation) == 0:
            print("%sitem" % indentation)
        elif verbose:
            print("%sList item" % indentation)
        if len(indentation) > 0 and verbose:
            print(i)
        if first:
            if print_first:
                print("%sFirst: %s" % (startLine, i))
            first = False

        if type(i) is dict:
            printDict(i, startLine)
        elif type(i) in simple_type_list:
            print("%s%s" % (startLine, i))
        else:
            print("%s Unexpected type in list %s" % (indentation, type(i)))

# listComponentTypes()

def summary(project="S"):
    print(" ===== Institutes =====")
    inst_output = "{name} ({code})"
    if sys.version_info[0] == 2:
        inst_output = u"{name} ({code})"

    printGetList("listInstitutions", method = "GET", output = inst_output)

    print(" ==== Strip component types =====")
    printGetList("listComponentTypes?project=%s" % project, method = "GET",
                 output = "{name} ({code})")
    # ({subprojects}) ({stages}) ({types})")

    # name, code
    #  Arrays: subprojects, stages, types

    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")

    print(" ==== Test types by component =====")
    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")
    for tc in type_codes:
        print("Test types for %s" % tc)
        printGetList("listTestTypes", {"project": project,
                                       "componentType": tc},
                     method = "GET", output = "  {name} ({code}) {state}")

# Produce some response without talking to DB
def doSomethingTesting(action, data = None, url = None, method = None,
                       attachments = None):
    if verbose:
        print("Testing request: %s" % action)
        print(" URL: %s" % url)
        print(" data: %s" % data)
        print(" method: %s" % method)
        print(" attachments: %s" % attachments)

    def encode(s):
        j = to_bytes(json.dumps(s))
        j = json.loads(j.decode("utf-8"))
        return j

    if action == "grantToken":
        return {'id_token': "1234567890abcdf"}
    if action == "listInstitutions":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
                {'code': 'UNIA', 'supervisor': u'First Second With\xe4t\xeda Last', 'name': u'Universit\xe4t A'}, {u'code': u'UNIB', u'supervisor': 'Other Name', 'name': 'University B'}
            ]})
    raise "Not known"
