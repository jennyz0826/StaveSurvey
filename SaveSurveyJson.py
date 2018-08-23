#import numpy as np
#import collections
import argparse
import json
import time
#import os, sys,
import ReadSurvey as RS

def ReadLines(infile):
    input = open(infile,"r")
    lines = input.readlines()
    input.close()
    return lines

def SaveJSON(survey,module,comp_code_path):
    lines=ReadLines(comp_code_path)

    line1,line2=lines[0].strip(),lines[1].strip()
    line1=line1.split(",")
    line2=line2.split(",")
    #print(line1)
    #print(line2)
    ind1=line1.index("Component_Code")
    ind2=line1.index("Institution")
    compCode=line2[ind1]
    inst=line2[ind2]

    DTO= {
            "component": compCode,
            "testType": "SURVY-A",
            "institution":inst,
            "runNumber": " ",
            "date": time.strftime("%d.%m.%Y"),
            "passed": survey.passed,
            "problems": not survey.passed,
            "properties": {
            "TIME": survey.gluetime
            },
            "results": {
                "IDEAL-A": survey.results['Ideal']['A'][0:2],
                "AG-A":  survey.results['AG']['A'][0:2],
                "BBR-A":  survey.results['BBR']['A'][0:2],
                "ABR-A":  survey.results['ABR']['A'][0:2]
                        }
            }
    out = json.dumps(DTO, indent=4) # sort_keys=True
    fname = "Module_%i.json" %module
    print("Saving %s" % fname)
    f = file(fname, 'w')
    f.write(out)
    f.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'read a survey file')

    parser.add_argument('--surveyPath', dest = 'survey_path', type = str, help = 'path to the survey')
    parser.add_argument('--module-num', dest= 'module_num',type=str,help='read survey file of these module, ex. 3,4,5')

    parser.add_argument('--compCodePath',dest='comp_code_path',type=str,help='path to find component code')
    #optional.add_argument('--getConfirm', dest = 'confirm', action = 'store_true', help = 'print survey stages')

    args = parser.parse_args()

    modules = [int(x) for x in args.module_num.split(",")]

    for module in modules:
        survey = RS.TheSurveys("Module" + str(module),"Module_" + str(module) + ".txt",
                    args.survey_path+"ModulePlacement/"+str(module)+"/")
        print(survey.name)
        print(survey.infile)
        survey.PrintTheFailures()
        SaveJSON(survey,module,args.comp_code_path)
