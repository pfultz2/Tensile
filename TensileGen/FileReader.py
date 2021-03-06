################################################################################
# Copyright (C) 2016 Advanced Micro Devices, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell cop-
# ies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IM-
# PLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNE-
# CTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
################################################################################

import argparse
import Structs
import SolutionCandidateGenerator

import xml.sax
import copy
import sys
import os

def addTimeToMap( psMap, exactMatch, problem, solution, time ):
  #print "prob" + str(problem.getSizeType()) + " - " + str(problem)
  if exactMatch.deviceProfile not in psMap:
    #print "XML Parser: b.adding %s" % exactMatch.deviceProfile.libString()
    psMap[exactMatch.deviceProfile] = {}
  if exactMatch not in psMap[exactMatch.deviceProfile]:
    #print "XML Parser:   b.adding %s" % exactMatch.libString()
    psMap[exactMatch.deviceProfile][exactMatch] = [{},{}]
  if problem not in psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()]:
    #print "XML Parser:     b.adding %s" % str(problem)
    psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem] = {}
  if solution not in psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem]:
    #print "XML Parser:       b.adding %s" % str(solution)
    psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution] = Structs.SolutionBenchmark()
  #print "XML Parser:       b.adding %f" % str(time)
  psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution].times.append(time)
  #print "size = ", len(psMap[exactMatch.deviceProfile][exactMatch][0]), len(psMap[exactMatch.deviceProfile][exactMatch][1])

def addValidationToMap( psMap, exactMatch, problem, solution, validationStatus ):
  if exactMatch.deviceProfile not in psMap:
    #print "XML Parser: v.adding %s" % exactMatch.deviceProfile.libString()
    psMap[exactMatch.deviceProfile] = {}
  if exactMatch not in psMap[exactMatch.deviceProfile]:
    #print "XML Parser:   v.adding %s" % exactMatch.libString()
    psMap[exactMatch.deviceProfile][exactMatch] = [{},{}]
  if problem not in psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()]:
    #print "XML Parser:     v.adding %s" % str(problem)
    psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem] = {}
  if solution not in psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem]:
    #print "XML Parser:       v.adding %s" % str(solution)
    psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution] = Structs.SolutionBenchmark()

  if psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution].validationStatus == 0:
    psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution].validationStatus = validationStatus
  elif psMap[exactMatch.deviceProfile][exactMatch][problem.getSizeType()][problem][solution].validationStatus != validationStatus:
    print "ERROR: conflicting validation reports"
  
def addProblemToTree( tree, exactMatch, problem ):
  if exactMatch.deviceProfile not in tree:
    #print "XML Parser: t.adding %s" % exactMatch.deviceProfile.libString()
    tree[exactMatch.deviceProfile] = {}
  if exactMatch not in tree[exactMatch.deviceProfile]:
    #print "XML Parser:   t.adding %s" % exactMatch.libString()
    tree[exactMatch.deviceProfile][exactMatch] = set()
  tree[exactMatch.deviceProfile][exactMatch].add(problem)



################################################################################
# TensileHandler
################################################################################
class TensileHandler( xml.sax.ContentHandler ):
  dbgPrint = False
  def __init__(self, data, readSolutions, optimizeAlpha, optimizeBeta):
    self.data = data
    self.readSolutions = readSolutions # read problems and solutions for GenBackend
    self.readProblems = not readSolutions # read problems only for GenBenchmark
    self.optimizeAlpha = optimizeAlpha
    self.optimizeBeta = optimizeBeta

    # for reading problems
    self.numProblemsAdded = 0
    self.problem = Structs.Problem()

    self.currentTensor = 0

    # for reading solutions
    self.solution = Structs.Solution()

  def startElement(self, tag, attributes):
    if self.dbgPrint:
      print "XML Parser: startElement(%s)" % tag
    if tag == "P": # DONE
      self.problem = Structs.Problem()

    elif tag == "TC": # DONE
      self.problem.tensorC.dataType.value = int(attributes["t"])
      n = int(attributes["n"])
      for i in range(0,n):
        dim = Structs.Dimension()
        dim.stride = int(attributes["st"+str(i)])
        dim.size = int(attributes["sz"+str(i)])
        self.problem.tensorC.dimensions.append(dim)

    elif tag == "TA": # DONE
      self.problem.tensorA.dataType.value = int(attributes["t"])
      n = int(attributes["n"])
      for i in range(0,n):
        dim = Structs.Dimension()
        dim.stride = int(attributes["st"+str(i)])
        dim.size = int(attributes["sz"+str(i)])
        self.problem.tensorA.dimensions.append(dim)

    elif tag == "TB": # DONE
      self.problem.tensorB.dataType.value = int(attributes["t"])
      n = int(attributes["n"])
      for i in range(0,n):
        dim = Structs.Dimension()
        dim.stride = int(attributes["st"+str(i)])
        dim.size = int(attributes["sz"+str(i)])
        self.problem.tensorB.dimensions.append(dim)

    elif tag == "O":
      self.problem.operation.type.value = int(attributes["t"])
      if self.optimizeAlpha:
        self.problem.operation.alphaType.value = int(attributes["a"])
      else:
        self.problem.operation.alphaType.value = self.problem.tensorC.dataType.value
      if self.optimizeBeta:
        self.problem.operation.betaType.value = int(attributes["b"])
      else:
        self.problem.operation.betaType.value = self.problem.tensorC.dataType.value
      self.problem.operation.useOffsets = int(attributes["o"])
      self.problem.operation.numIndicesFree = int(attributes["nF"])
      self.problem.operation.numIndicesBatch = int(attributes["nB"])
      self.problem.operation.numIndicesSummation = int(attributes["nS"])
      
    elif tag == "IA":
      n = int(attributes["n"])
      for i in range(0,n):
        self.problem.operation.indexAssignmentsA.append(int(attributes["i"+str(i)]))
      
    elif tag == "IB":
      n = int(attributes["n"])
      for i in range(0,n):
        self.problem.operation.indexAssignmentsB.append(int(attributes["i"+str(i)]))
      
    elif tag == "DP":
      n = int(attributes["n"])
      for i in range(0,n):
        name = attributes["d"+str(i)]
        for j in range(0,len(name)):
          if not name[j].isalnum():
            name = name[:j] + "_" + name[j+1:]
        numComputeUnits = int(attributes["CU"+str(i)])
        clockFrequency = int(attributes["MHz"+str(i)])
        flopsPerClock = int(attributes["FPC"+str(i)])
        self.problem.deviceProfile.devices.append(Structs.Device( name, numComputeUnits, clockFrequency, flopsPerClock ))
      
    elif tag == "ID" and self.readSolutions:
      self.solution.kernels = []
      for i in range(0,4):
        self.solution.kernels.append(None)
      self.solution.kernelGrid = [ int(attributes["kG0"]), int(attributes["kG1"]), int(attributes["kG2"]) ]
      self.solution.branch = [ Structs.BranchType(int(attributes["b0"])), Structs.BranchType(int(attributes["b1"])) ]
      self.solution.ppdOffsets = int(attributes["ppdO"])
      self.solution.ppdLeadingStrides = int(attributes["ppdLS"])
      self.solution.ppdAll = int(attributes["ppdAll"])
      
    elif tag == "K" and self.readSolutions:
      # read data from xml
      i = int(attributes["i"])
      self.solution.kernels[i] = Structs.Kernel()
      self.solution.kernels[i].tile.workGroup = [int(attributes["wG0"]), int(attributes["wG1"])]
      self.solution.kernels[i].tile.microTile = [int(attributes["mT0"]), int(attributes["mT1"])]
      self.solution.kernels[i].tile.branch = [ Structs.BranchType(int(attributes["b0"])), Structs.BranchType(int(attributes["b1"])) ]
      self.solution.kernels[i].numLoadsParaA        = int(attributes["nlpaA"])
      self.solution.kernels[i].loadSizeParaA        = int(attributes["lspaA"])
      self.solution.kernels[i].totalLoadSizeParaA   = int(attributes["tspaA"])
      self.solution.kernels[i].numLoadsPerpA        = int(attributes["nlpeA"])
      self.solution.kernels[i].loadSizePerpA        = int(attributes["lspeA"])
      self.solution.kernels[i].totalLoadSizePerpA   = int(attributes["tspeA"])
      self.solution.kernels[i].numLoadsParaB        = int(attributes["nlpaB"])
      self.solution.kernels[i].loadSizeParaB        = int(attributes["lspaB"])
      self.solution.kernels[i].totalLoadSizeParaB   = int(attributes["tspaB"])
      self.solution.kernels[i].numLoadsPerpB        = int(attributes["nlpeB"])
      self.solution.kernels[i].loadSizePerpB        = int(attributes["lspeB"])
      self.solution.kernels[i].totalLoadSizePerpB   = int(attributes["tspeB"])
      self.solution.kernels[i].unrolls = [ int(attributes["u0"]) ]
      secondUnroll = int(attributes["u1"])
      if secondUnroll > 0:
        self.solution.kernels[i].unrolls.append( secondUnroll )
      # pull data from problem and solution
      self.solution.kernels[i].dataTypeC = self.problem.tensorC.dataType
      self.solution.kernels[i].dataTypeA = self.problem.tensorA.dataType
      self.solution.kernels[i].dataTypeB = self.problem.tensorB.dataType
      self.solution.kernels[i].dataTypeAlpha = self.problem.operation.alphaType
      self.solution.kernels[i].dataTypeBeta = self.problem.operation.betaType
      #kernel.operation = self.problem.operation
      self.solution.kernels[i].problem = self.problem
      self.solution.kernels[i].ppdOffsets = self.solution.ppdOffsets
      self.solution.kernels[i].ppdLeadingStrides = self.solution.ppdLeadingStrides
      self.solution.kernels[i].ppdAll = self.solution.ppdAll
      # make index assignments (rather than storing in xml)
      SolutionCandidateGenerator.makeIndexAssignments(self.solution.kernels[i], self.problem)

    elif tag == "B" and self.readSolutions:
      # basically end of TraceEntry
      time = float(attributes["t"])
      exactMatch = Structs.ExactMatch()
      self.assignExactMatch(exactMatch)
      addTimeToMap( self.data, exactMatch, copy.deepcopy(self.problem), copy.deepcopy(self.solution), time )

    elif tag == "V" and self.readSolutions:
      valid = 1 if attributes["s"] == "P" else -1
      exactMatch = Structs.ExactMatch()
      self.assignExactMatch(exactMatch)
      addValidationToMap( self.data, exactMatch, copy.deepcopy(self.problem), copy.deepcopy(self.solution), valid )

  def endElement(self, tag):
    if self.dbgPrint:
      print "XML Parser: endElement(%s)" % tag
    if tag == "P": # DONE
      if self.readProblems:
        # self.data.add(copy.deepcopy(self.problem))
        exactMatch = Structs.ExactMatch()
        self.assignExactMatch(exactMatch)
        exactMatch.ppdOffsets = 0
        exactMatch.ppdLeadingStrides = 0
        exactMatch.ppdAll = 0
        addProblemToTree( self.data, exactMatch, copy.deepcopy(self.problem) )
        self.numProblemsAdded += 1
    elif tag == "T": # DONE
      pass

  def characters(self, content):
    pass

  def assignExactMatch(self, exactMatch):
    exactMatch.deviceProfile = self.problem.deviceProfile
    exactMatch.numIndicesFree = len(self.problem.tensorC.dimensions)
    exactMatch.indexAssignmentsA = self.problem.operation.indexAssignmentsA
    exactMatch.indexAssignmentsB = self.problem.operation.indexAssignmentsB
    exactMatch.operationType = self.problem.operation.type
    exactMatch.ppdOffsets = self.solution.ppdOffsets
    exactMatch.ppdLeadingStrides = self.solution.ppdLeadingStrides
    exactMatch.ppdAll = self.solution.ppdAll
    exactMatch.typeC = self.problem.tensorC.dataType
    exactMatch.typeA = self.problem.tensorA.dataType
    exactMatch.typeB = self.problem.tensorB.dataType
    exactMatch.typeAlpha = self.problem.operation.alphaType
    exactMatch.typeBeta = self.problem.operation.betaType



################################################################################
# getProblemsFromXML
################################################################################
def getProblemsFromXML( inputFile, problemTree, optimizeAlpha, optimizeBeta ):
  parser = xml.sax.make_parser()
  parser.setFeature(xml.sax.handler.feature_namespaces, 0)
  readSolutions = False
  appProblemsHandler = TensileHandler(problemTree, readSolutions, optimizeAlpha, optimizeBeta)
  parser.setContentHandler( appProblemsHandler )
  #try:
  parser.parse( inputFile )
  print "  + " + str(appProblemsHandler.numProblemsAdded) \
      + " problem(s) from " + os.path.basename(inputFile)
  #except:
  #  print inputFile + " error"

################################################################################
# getProblemsFromXML
################################################################################
def getSolutionsFromXML( inputFile, psMap, optimizeAlpha, optimizeBeta ):
  parser = xml.sax.make_parser()
  parser.setFeature(xml.sax.handler.feature_namespaces, 0)
  readSolutions = True
  solutionsHandler = TensileHandler(psMap, readSolutions, optimizeAlpha, optimizeBeta)
  parser.setContentHandler( solutionsHandler )
  #try:
  #print "XML Parser: parsing %s" % str(inputFile)
  parser.parse( inputFile )
  #except:
  #  print inputFile + " error"
  

################################################################################
# Main
################################################################################
#if __name__ == "__main__":
#
#  # arguments
#  ap = argparse.ArgumentParser(description="FileReader")
#  ap.add_argument("--input-file", dest="inputFiles", action="append" )
#  args = ap.parse_args()
#
#  # parse xml
#  for inputFile in args.inputFiles:
#    problemSet = set()
#    getProblemsFromXML( inputFile, problemSet )
#  print problemSet
