
import argparse
import json
import os, sys
import numpy as np
import ReadSurvey as RS
import time
import upload_test_results as uploadTest



class Error(Exception):
    pass

class GeneralError(Error):
    def __init__(self, message):
        self.message = message

def INFO(string):
    print('[INFO]$ ' + string)

def PROMPT(string):
    print('[PROMPT]$ ' + string)

def WARNING(string):
    print('[WARNING]$ ' + string)

def ERROR(string):
    print('[ERROR]$ ' + string)

def STATUS(string):
    print('[STATUS]$ ' + string)

def ReadLines(infile):
    input = open(infile,"r")
    lines = input.readlines()
    input.close()
    return lines

def FillResults(survey,stage):
    null=[-0.1,-0.1] #cannot be nan
    result=[]
    for corner in survey.corners.keys():

        if stage in survey.stages:
            result.append(survey.results[stage][corner][0:2])
        else:
            result.append(null)

    return result

def GetCompCode(comp_code_path):
    lines=ReadLines(comp_code_path)

    line1,line2=lines[0].strip(),lines[1].strip()
    line1=line1.split(",")
    line2=line2.split(",")

    ind1=line1.index("Component_Code")
    ind2=line1.index("Institution")
    compCode=line2[ind1]
    inst=line2[ind2]

    return compCode, inst

def GetAssemblerSite():

    global assemblers,site
    assemblers=raw_input("Hi assemblers, please insert your names here:")

    while assemblers=='':
        PROMPT('No assembler name was inserted, please insert your names here:')
        assemblers=raw_input()

    site=raw_input("Assembly Site:")

    while site=='':
        PROMPT('Invalid input, please insert assembly site here:')
        site=raw_input()


def TestToUpload():
    tests=["SURVEY-AG","SURVEY-BBR"]
    print("Tests for a stave:")
    for ind, test in enumerate(tests):
        print("%i.  %s" % (ind+1, test))
    PROMPT('Please enter the indices for the tests you would like to upload, separated by "," or "all":')
    while True:
        response=raw_input().strip()
        try:
            if response=='':
                PROMPT('INSERT INDICES HERE:')
                continue
            #response=raw_input().strip().split(",")
            elif response=='none':
                INFO('will not upload any test')
                return []
                break
            elif response=='all':
                indices=np.arange(0,len(tests),1)
            else:
                indices=[int(i)-1 for i in response.split(",")]
            return [tests[i] for i in indices]
            break

        except ValueError:
            del response
            PROMPT('Invalid input. Please enter INDICES for the tests,separated by "," or "all":')
            continue
        except IndexError:
            del response
            PROMPT('Invalid index. Please enter INDICES for the tests,separated by "," or "all":')
            continue



def GetAGJSON(survey,module,comp_code_path):

    compCode, inst = GetCompCode(comp_code_path)
    AG_result=FillResults(survey,"AG")
    DTO = {  "component": compCode,
             "testType": "SURVEY-AG",
             "institution": inst,
             "runNumber": "1-1",
             "date": time.strftime("%d.%m.%Y"),
             "passed": survey.passed,
             "problems": not survey.passed,
             "properties": {
                "MODULE_NUM": survey.name,
                "GLUETIME": survey.gluetime,
                "FIDUCIAL": "Mark E",
                "ASSEMBLER": assemblers,
                "SITE": site
                 },
             "results": {
                "A": AG_result[0],
                "B": AG_result[1],
                "C": AG_result[2],
                "D": AG_result[3]

                 }}

    out = json.dumps(DTO, indent=4) # sort_keys=True
    #fname = "Module_%i.json" %module
    STATUS("generated json for module %i" % module)
    #print (out)
#    f = file(fname, 'w')#
#    f.write(out)
#    f.close()
    return out

def GetBBRJSON(survey,module,comp_code_path):
    compCode, inst = GetCompCode(comp_code_path)
    BBR_result=FillResults(survey,"BBR")

    DTO={
        "component": compCode,
        "testType": "SURVEY-BBR",
        "institution": inst,
        "runNumber": "1-1",
        "date": time.strftime("%d.%m.%Y"),
        "passed": survey.passed,
        "problems": not survey.passed,
        "properties": {
        "MODULE_NUM": survey.name,
        "FIDUCIAL": "MarkE",
        "ASSEMBLER": assemblers
        },
        "results": {
        "A": BBR_result[0],
        "B": BBR_result[1],
        "C": BBR_result[2],
        "D": BBR_result[3]
                }
        }
    out = json.dumps(DTO, indent=4)
        #fname = "Module_%i.json" %module
    STATUS("generated json for module %i" % module)
    #print (out)

    return out

def main(args):
    print('')
    print('*************************************************************************')
    print('* *                                                                 *   *')
    print('*                            uploadStaveAssemblySurvey.py               *')
    print('* *                                                                 *   *')
    print('*************************************************************************')
    print('')

    try:

        missing_args=[]
        if args.survey_path == None:
            missing_args.append('--surveyPath')
        if args.module_num ==None:
            missing_args.append('--module-num')
        if args.comp_code_path==None:
            missing_args.append('--compCodePath')

        if missing_args !=[]:
            raise GeneralError('missing arguments:'+','.join(missing_args)+'.')

        if not os.path.exists(args.survey_path):
            raise GeneralError('--surveyPath does not exist: ' + os.path.abspath(args.survey_path))
        if not os.path.exists(args.comp_code_path):
            raise GeneralError('--compCodePath does not exist: ' + os.path.abspath(args.comp_code_path))


        if args.module_num != "all":
            modules=[int(x) for x in args.module_num.split(",")]
        else:
            modules = np.arange(1,14,1)

        assemblers=GetAssemblerSite()
        tests=TestToUpload()
        if tests==[]:
            exit()
        for module in modules:
            survey = RS.TheSurveys("Module" + str(module),"Module_" + str(module) + ".txt",
                    args.survey_path+"ModulePlacement/"+str(module)+"/")
        #print(survey.name)
        #print(survey.infile)

            if survey.glued:
                if args.Testing is False:
                    import dbAccess

                    if os.getenv("ITK_DB_AUTH"):
                        dbAccess.token = os.getenv("ITK_DB_AUTH")

                    if "SURVEY-AG" in tests:
                        testFile1=GetAGJSON(survey,module,args.comp_code_path)
                        dbAccess.doSomething("uploadTestRunResults", json.loads(testFile1))

                    if "SURVEY-BBR" in tests:
                        testFile2=GetBBRJSON(survey,module,args.comp_code_path)
                        dbAccess.doSomething("uploadTestRunResults", json.loads(testFile2))
                print("%s passed:" % survey.name, survey.passed)



                else:
                    STATUS("------Testing uploadStaveAssemblySurvey.py------")
                    survey.PrintTheFailures()
            else:
                print("%s not glued or survey information not in %s" % (survey.name,survey.infile))
            print("------------------------------------------")
    except GeneralError as e:
        ERROR(e.message)
        STATUS('Finished with error.\n')
        sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'read a survey file')

    parser._action_groups.pop()

    required=parser.add_argument_group('required arguments')
    required.add_argument('--surveyPath', dest = 'survey_path', type = str, help = 'path to the ModulePlacement/')
    required.add_argument('--module-num', dest= 'module_num',type=str,
                            help='module numbers (ex. 3,4,5); or write "all" if want to upload all modules ')

    required.add_argument('--compCodePath',dest='comp_code_path',type=str,help='path to find component code')

    optional = parser.add_argument_group('optional arguments')
    optional.add_argument('--testing', dest = 'Testing', action = 'store_true', help = 'if only testing and DO NOT upload')

    args = parser.parse_args()

    main(args)
