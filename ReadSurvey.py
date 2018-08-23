#!/bin/env python3
import numpy as np
#import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import collections
import argparse
#import pandas as pd


def StringtoFlt(string):
    flt = None
    if ("\n" in string):
        string.replace("\n", "")
    if ("=" in string):
        string = string[string.find("=") + 1:]
    try:
        flt = float(string)
    except ValueError:
        print("Cannot convert string to float!")
    return flt

def RepealAndReplace(string, repeal, replace = 1):
    if (repeal in string):
        ind = string.index(repeal)
        string = string[0 : ind + replace] + string[ind + len(repeal) : ]
    return string

def RenameStages(stages):
    output = []
    for ind,stage in enumerate(stages):

        stage = RepealAndReplace(stage, 'Right', 0)
        stage = RepealAndReplace(stage, 'Before')
        stage = RepealAndReplace(stage, 'After')
        stage = RepealAndReplace(stage, 'Gluing')
        stage = RepealAndReplace(stage, 'Bridge') #, 2),Changed this, otherwise -- BBrR
        stage = RepealAndReplace(stage, 'Removal')
        while ('_' in stage):
            stage = stage.replace('_','')

        BBR1=-1
        ABR1=-1
        if "BBR" in stage:
            if BBR1 == -1:
                BBR1=ind
                stage="BBR"
        if "ABR" in stage:
            if ABR1 == -1:
                BBR1=ind
                stage="ABR"
        output.append(stage)
    #print(output)
    return output

class TheSurveys(object):
    def __init__(self, name, infile, dir):
        self.name = name
        self.infile = dir + infile
        self.lines = self.GetLines()
        self.corners = self.SeparateByCorner()
        self.stages = self.GetStages()
        self.gluetime=self.GetGlueTime()
        self.results = self.GetResults()
        self.tolerance = 25
        self.passed, self.failures = self.DidItPass()
        self.glued = self.WasItGlued()

    def GetLines(self):
        input = open(self.infile,"r")
        lines = input.readlines()
        input.close()
        return lines

    def SeparateByCorner(self):
        indA, indB, indC, indD = 0, 0, 0, 0
        for ind, line in enumerate(self.lines):
            if ("CornerA" in line):
                indA = ind + 1
            elif ("CornerB" in line):
                indB = ind + 1
            elif ("CornerC" in line):
                indC = ind + 1
            elif ("CornerD" in line):
                indD = ind + 1

        corners = collections.OrderedDict()
        corners['A'] = self.lines[indA : indB - 2]
        corners['B'] = self.lines[indB : indC - 2]
        corners['C'] = self.lines[indC : indD - 2]
        corners['D'] = self.lines[indD : ]

        return corners

    def GetStages(self):
        stages = []
        for line in self.corners['A']:
            stage = line[line.find("_") + 1: line.find("=") - 1]
            if (stage not in stages):
                stages.append(stage)
        stages = RenameStages(stages)
        if "AG" not in stages:
            print("WARNING: no AG for %s." %self.name)
        if "BBR" not in stages:
            print("WARNING: no BBR for %s, possibly glue not cured yet." %self.name)
        if "ABR" not in stages:
            print("WARNING: no ABR for %s, possibly bridge not removed yet" %self.name)
        return stages

    def GetGlueTime(self):
        DateAndTime = []
        for line in self.lines:
            if ("Date_" in line):
                DateAndTime.append(line)
        #print DateAndTime
        allstages=self.stages
        if "AG" in allstages:
            ind=allstages.index("AG") +1
            line=DateAndTime[ind]
            gluetime=line[line.find("=")+3:line.find(".")-4]
            print("Date and time of gluing:",gluetime)
        else:
            gluetime="00:00:00"
            #print(ind)
        return gluetime


    def GetResults(self):
        results = collections.OrderedDict()

        for ind, stage in enumerate(self.stages):
            results[stage] = collections.OrderedDict()
            for corner in self.corners.keys():
                results[stage][corner] = []
                for xyz in range(3):
                    pos = StringtoFlt(self.corners[corner][(3 * ind) + xyz])
                    results[stage][corner].append(pos)
        return results



    def DidItPass(self):
        dims = ['X', 'Y']
        passed = True
        failures = []
        for xyz, dim in enumerate(dims):
            for corner in self.corners.keys():
                for stage in self.stages:
                    movement = 1000 * (self.results[stage][corner][xyz] - self.results[self.stages[0]][corner][xyz])
                    if (abs(movement) >= self.tolerance):
                        passed = False
                        failures.append(corner + ' - ' + stage + ': delta' + dim + ' = ' + str(movement) + ' um')
        return passed, failures

    def WasItGlued(self):
        glued=True
        stages=self.stages
        if "AG" not in stages and "ABR" not in stages and "BBR" not in stages:
            glued=False
        return glued

    def PrintTheFailures(self):
        print('')
        print('----------------------------------------')
        if self.passed:
            print("Passed! All surveys within " + str(self.tolerance) + " um tolerance.")
        else:
            print("Failed! The following corners are out of " + str(self.tolerance) + " um tolerance: ")
            for failure in self.failures:
                print(failure)
        print('----------------------------------------')
        print('')


if __name__ == '__main__':

    # Define our parser
    parser = argparse.ArgumentParser(description = 'read a survey file')
    #parser._action_groups.pop()

    # Define our required arguments
    #required = parser.add_argument_group('required arguments')
    parser.add_argument('--surveyPath', dest = 'survey_path', type = str, help = 'path to the survey')
    parser.add_argument('--module-num', dest= 'module_num',type=int,help='read survey file of this module')
    # Define our optional arguments
    #optional = parser.add_argument_group('optional arguments')

    #optional.add_argument('--getConfirm', dest = 'confirm', action = 'store_true', help = 'print survey stages')

    args = parser.parse_args()

    modules = [args.module_num]
    for module in modules:
        survey = TheSurveys("Module" + str(module), "Module_" + str(module) + ".txt",args.survey_path)

        print(survey.name)
        print(survey.infile)

        survey.PrintTheFailures()
