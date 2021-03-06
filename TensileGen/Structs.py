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

import SolutionCandidateGenerator

################################################################################
# Status - Enum
################################################################################
class Status:
  success = 0

################################################################################
# Data Type - Enum
################################################################################
class DataType:
  single        = 0
  double        = 1
  complexSingle = 2
  complexDouble = 3
  complexConjugateSingle = 4
  complexConjugateDouble = 5
  
  half          = 6
  complexHalf   = 7
  complexConjugateHalf   = 8

  # num         = 9
  none          = 10

  def __init__( self, value ):
    self.value = value

  def toChar(self):
    if self.value == self.half:
      return "H"
    if self.value == self.single:
      return "S"
    elif self.value == self.double:
      return "D"
    elif self.value == self.complexHalf:
      return "Q"
    elif self.value == self.complexSingle:
      return "C"
    elif self.value == self.complexDouble:
      return "Z"
    elif self.value == self.complexConjugateHalf:
      return "W"
    elif self.value == self.complexConjugateSingle:
      return "X"
    elif self.value == self.complexConjugateDouble:
      return "Y"
    elif self.value == self.none:
      return "0"
    else:
      return "ERROR(" + str(self.value) + ")"

  def toOpenCL(self):
    if self.value == self.single:
      return "float"
    elif self.value == self.double:
      return "double"
    elif self.value == self.complexSingle or self.value == self.complexConjugateSingle:
      return "float2"
    elif self.value == self.complexDouble or self.value == self.complexConjugateDouble:
      return "double2"
    else:
      return "ERROR(" + str(self.value) + ")"

  def toHIP(self):
    if self.value == self.single:
      return "float"
    elif self.value == self.double:
      return "double"
    elif self.value == self.complexSingle or self.value == self.complexConjugateSingle:
      return "float_2"
    elif self.value == self.complexDouble or self.value == self.complexConjugateDouble:
      return "double_2"
    else:
      return "ERROR(" + str(self.value) + ")"

  def toDevice(self, backend):
    if backend.isOpenCL():
      return self.toOpenCL()
    else:
      return self.toHIP()

  def toCpp(self):
    if self.value == self.single:
      return "float"
    elif self.value == self.double:
      return "double"
    elif self.value == self.complexSingle or self.value == self.complexConjugateSingle:
      return "TensileComplexFloat"
    elif self.value == self.complexDouble or self.value == self.complexConjugateDouble:
      return "TensileComplexDouble"
    elif self.value == self.none:
      return "void"
    else:
      return "ERROR(" + str(self.value) + ")"

  def getLibString(self):
    if self.value == self.half:
      return "tensileDataTypeHalf"
    if self.value == self.single:
      return "tensileDataTypeSingle"
    elif self.value == self.double:
      return "tensileDataTypeDouble"
    elif self.value == self.complexHalf:
      return "tensileDataTypeComplexHalf"
    elif self.value == self.complexSingle:
      return "tensileDataTypeComplexSingle"
    elif self.value == self.complexDouble:
      return "tensileDataTypeComplexDouble"
    elif self.value == self.complexConjugateHalf:
      return "tensileDataTypeComplexConjugateHalf"
    elif self.value == self.complexConjugateSingle:
      return "tensileDataTypeComplexConjugateSingle"
    elif self.value == self.complexConjugateDouble:
      return "tensileDataTypeComplexConjugateDouble"
    elif self.value == self.none:
      return "tensileDataTypeNone"
    else:
      return "ERROR(" + str(self.value) + ")"

  def zeroStringOpenCL(self):
    zeroString = "("
    zeroString += self.toOpenCL()
    zeroString += ")("
    if self.isReal():
      zeroString += "0.0"
    else:
      zeroString += "0.0, 0.0"
    zeroString += ")"
    return zeroString

  def zeroStringHIP(self):
    zeroString = ""
    zeroString += self.toHIP()
    zeroString += "("
    if self.isReal():
      zeroString += "0.0"
    else:
      zeroString += "0.0, 0.0"
    zeroString += ")"
    return zeroString

  def isReal(self):
    if self.value == self.half or self.value == self.single or self.value == self.double:
      return True
    else:
      return False

  def isComplex(self):
    return not self.isReal()

  def isConjugate(self):
    if self.value == self.complexConjugateHalf or self.value == self.complexConjugateSingle or self.value == self.complexConjugateDouble:
      return True
    else:
      return False

  def isDouble(self):
    if self.value == self.double or self.value == self.complexDouble or self.value == self.complexConjugateDouble:
      return True
    else:
      return False


  def numRegisters( self ):
    if self.value == self.single:
      return 1
    elif self.value == self.double:
      return 2
    elif self.value == self.complexSingle or self.value == self.complexConjugateSingle:
      return 2
    elif self.value == self.complexDouble or self.value == self.complexConjugateDouble:
      return 4
    else:
      return "ERROR(" + str(self.value) + ")"

  def numBytes( self ):
    return self.numRegisters() * 4

  def __str__(self):
    return self.toChar()

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return (self.value)
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, DataType) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Dimension
################################################################################
class Dimension:
  def __init__( self ):
    self.stride = 0
    self.size = 0
  #def __init__( self, stride, size ):
  #  self.stride = stride
  #  self.size = size

  def __str__(self):
    return "["+str(self.stride)+","+str(self.size)+"]"

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( self.stride, self.size )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Dimension) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Tensor
################################################################################
class Tensor:
  def __init__( self ):
    self.dataType = DataType(-1)
    self.dimensions = []
    #print "Tensor::__init__" + str(self)

  def __str__(self):
    state = "[Tensor"
    state += "; " + self.dataType.toChar()
    state += "; " + str(self.dimensions)
    state += "]"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( self.dataType, tuple(self.dimensions))
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Tensor) \
        and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Backend - Enum
################################################################################
class Backend:
  opencl12 = 0
  hip = 1

  def __init__( self ):
    self.value = 0

  def __str__(self):
    if self.value == self.opencl12:
      return "OpenCL 1.2"
    elif self.value == self.hip:
      return "HIP"
    else:
      return "ERROR"

  def isHIP(self):
    return self.value == self.hip

  def isOpenCL(self):
    return self.value == self.opencl12

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( self.value )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Backend) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Device
################################################################################
class Device:
  def __init__( self, name, numComputeUnits, clockFrequency, flopsPerClock):
    self.name = name
    self.numComputeUnits = numComputeUnits
    self.clockFrequency = clockFrequency
    self.flopsPerClock = flopsPerClock

  def __str__(self):
    print "Device.str"
    state = "[Device"
    state += "; " + self.name
    state += "; " + str(self.numComputeUnits)
    state += "; " + str(self.clockFrequency)
    state += "; " + str(self.flopsPerClock)
    state += "]"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        self.name, \
        self.numComputeUnits, \
        self.clockFrequency, \
        self.flopsPerClock, \
        )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Device) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# DeviceProfile
################################################################################
class DeviceProfile:
  def __init__(self):
    self.devices = []

  def libString(self):
    s = self.devices[0].name
    for i in range( 1, len(self.devices)):
      s += "_" + self.devices[i].name
    return s

  def __str__(self):
    print "DeviceProfile.str"
    return str(self.devices)

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return (tuple(self.devices))
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, DeviceProfile) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# OperationType - Enum
################################################################################
class OperationType:
  contraction = 0
  convolution = 1
  correlation = 2

  def __init__(self, value):
    self.value = value

  def __str__(self):
    if self.value == self.contraction:
      return "CT"
    elif self.value == self.convolution:
      return "CV"
    elif self.value == self.correlation:
      return "CR"
    else:
      return "ERROR"

  def __repr__(self):
    return self.__str__()

  def getLibString(self):
    if self.value == self.contraction:
      return "tensileOperationTypeContraction"
    elif self.value == self.convolution:
      return "tensileOperationTypeConvolution"
    elif self.value == self.correlation:
      return "tensileOperationTypeCorrelation"
    else:
      return "ERROR"


  def getAttributes(self):
    return (self.value)
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, OperationType) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Operation
################################################################################
class Operation:
  def __init__( self ):
    self.type = OperationType(-1)
    #self.useAlpha = -1
    self.alphaType = DataType(-1)
    #self.useBeta = -1
    self.betaType = DataType(-1)
    self.useOffsets = -1
    self.numIndicesFree = -1
    self.numIndicesBatch = -1
    self.numIndicesSummation = -1
    self.indexAssignmentsA = []
    self.indexAssignmentsB = []
    self.pad = []
    self.stride = []

  def __str__(self):
    state = ""
    state += "[Operation"
    state += "; " + str(self.type)
    #state += "; " + str(self.useAlpha)
    state += "; " + str(self.alphaType)
    #state += "; " + str(self.useBeta)
    state += "; " + str(self.betaType)
    state += "; " + str(self.useOffsets)
    state += "; " + str(self.numIndicesFree)
    state += "; " + str(self.numIndicesBatch)
    state += "; " + str(self.numIndicesSummation)
    state += "; " + str(self.indexAssignmentsA)
    state += "; " + str(self.indexAssignmentsB)
    state += "]"
    return state

  def useAlpha(self):
    return self.alphaType.value != DataType.none
  def useBeta(self):
    return self.betaType.value != DataType.none

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        self.type, \
        self.alphaType, \
        self.betaType, \
        self.useOffsets, \
        self.numIndicesFree, \
        self.numIndicesBatch, \
        self.numIndicesSummation, \
        tuple(self.indexAssignmentsA), \
        tuple(self.indexAssignmentsB), \
        )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Operation) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# ExactMatch - parameters which must exactly match between problem and solution
################################################################################
class ExactMatch:
  indexChars = "ijklmnopqrstuvwxyz"
  def __init__(self):
    self.deviceProfile = DeviceProfile()
    self.typeC = DataType(-1)
    self.typeA = DataType(-1)
    self.typeB = DataType(-1)
    self.typeAlpha = DataType(-1)
    self.typeBeta = DataType(-1)
    self.operationType = OperationType(-1)
    self.numIndicesFree = -1
    self.indexAssignmentsA = []
    self.indexAssignmentsB = []
    self.ppdOffsets = 0 # if true, solution must allow offset parameters; if false, enqueue must not use offsets
    self.ppdLeadingStrides = 0 # if true, solution must allow non-1 initial strides; if false, problem must have size=1 initial strides
    self.ppdAll = 0 # to actually support all parameters being compiled into kernel, all tensor dimensions must become part of exact match

  def __str__(self):
    return self.libString()

  def libString(self):
    state = ""
    state += self.deviceProfile.libString()
    state += "_"
    state += str(self.operationType)
    state += "_"
    state += self.typeC.toChar().upper()
    state += self.typeA.toChar().upper()
    state += self.typeB.toChar().upper()
    state += self.typeAlpha.toChar().upper()
    state += self.typeBeta.toChar().upper()
    state += "_"
    # C dimensions
    state += "C"
    for i in range(0, self.numIndicesFree):
      state += self.indexChars[i].lower()
    # A dimensions
    state += "_A"
    for i in self.indexAssignmentsA:
      state += self.indexChars[i].lower()
    # B dimensions
    state += "_B"
    for i in self.indexAssignmentsB:
      state += self.indexChars[i].lower()

    # optimization level
    ppdStr = ""
    if self.ppdOffsets and not self.ppdLeadingStrides:
      ppdStr = "O1"
    elif not self.ppdOffsets and self.ppdLeadingStrides:
      ppdStr = "O2"
    elif self.ppdOffsets and self.ppdLeadingStrides and not self.ppdAll:
      ppdStr = "O3"
    elif self.ppdAll:
      ppdStr = "04"
    else:
      ppdStr = "O0"
    state += "_" + ppdStr
    # when selecting a kernel, the ppd must match so that kernel arguments are same, but
    # since ExactMatch is only ever converted to string to describe a problem only and
    # ppd is implementation detail, we can avoid attaching ppd to ExactMatch string
    # resulting in a cleaner output
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
      self.deviceProfile, \
      self.typeC, \
      self.typeA, \
      self.typeB, \
      self.typeAlpha, \
      self.typeBeta, \
      self.operationType, \
      tuple(self.indexAssignmentsA), \
      tuple(self.indexAssignmentsB), \
      self.ppdOffsets, \
      self.ppdLeadingStrides \
      )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, ExactMatch) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result

class SolutionBenchmark:
  def __init__(self):
    self.times = []
    self.validationStatus = 0 # -1 invalid, 0 unspecified, +1 valid

################################################################################
# Problem
# - some problem descriptors get passed in as kernel argument and
#   Don't need to be exactly matched to solution
#   - Tensor dimensions[i].size
#   - Tensor dimensions[i].stride
#   - alpha
#   - beta
# - some problem descriptors get compiled/written into kernel and
#   Do need to be exactly matched to solution
#   - Tensor data types
#   - dimensionality of tensors and operation
#   - operation
# - other
#   - Device - determined through benchmarking / file reading
################################################################################
class Problem:
  # sizeType=0 ranged
  # sizeType=1 exact
  def __init__( self ):
    self.tensorC = Tensor()
    self.tensorA = Tensor()
    self.tensorB = Tensor()
    self.operation = Operation()
    self.deviceProfile = DeviceProfile()
    self.sizeFree = 0
    self.sizeType = -1
    self.totalFlops = -1
    self.size0 = -1
    self.size1 = -1
    self.sizeU = -1

  def getSizeFree(self):
    if self.sizeFree == 0:
      self.sizeFree = 1
      for dimension in self.tensorC.dimensions:
        self.sizeFree *= dimension.size
    return self.sizeFree

  def getSize01U(self):
    if self.size0 < 0:
      kernel = Kernel()
      SolutionCandidateGenerator.makeIndexAssignments(kernel, self)
      self.size0 = self.tensorC.dimensions[ kernel.indexAssignmentDim0].size
      self.size1 = self.tensorC.dimensions[ kernel.indexAssignmentDim1].size
      self.sizeU = -1
      for i in range(len(self.operation.indexAssignmentsA)):
        if kernel.indexUnroll == self.operation.indexAssignmentsA[i]:
          self.sizeU = self.tensorA.dimensions[i].size
          break
    return (self.size0, self.size1, self.sizeU)

  def getSizeType(self):
    if self.sizeType < 0:
      # make index assignments
      kernel = Kernel()
      SolutionCandidateGenerator.makeIndexAssignments(kernel, self)
      # get key sizes
      problemSizeDim0 = self.tensorC.dimensions[ kernel.indexAssignmentDim0].size
      problemSizeDim1 = self.tensorC.dimensions[ kernel.indexAssignmentDim1].size
      problemSizeUnroll = -1
      for i in range(len(self.operation.indexAssignmentsA)):
        if kernel.indexUnroll == self.operation.indexAssignmentsA[i]:
          problemSizeUnroll = self.tensorA.dimensions[i].size
          break
      # if sizes are squarish, then type=0
      self.sizeType = 0
      if (not problemSizeDim0 % 16 == 0 and not (problemSizeDim0+1) % 16 == 0) or (not problemSizeDim1 % 16 == 0 and not (problemSizeDim1+1) % 16 == 0) or (not problemSizeUnroll % 16 == 0 and not (problemSizeUnroll+1) % 16 == 0):
        self.sizeType = 1
      if abs(problemSizeDim0-problemSizeDim1) > 1 or abs(problemSizeDim0-problemSizeUnroll) > 1 or abs(problemSizeDim1-problemSizeUnroll) > 1:
        self.sizeType = 1
    return self.sizeType

  def getNumFlops(self):
    if self.totalFlops < 0:
      self.totalFlops = self.getSizeFree()
      if self.tensorA.dataType.isReal():
        self.totalFlops *= 2
      else:
        self.totalFlops *= 8
      for i in range(0, len(self.operation.indexAssignmentsA)):
        index = self.operation.indexAssignmentsA[i]
        inC = index < len(self.tensorC.dimensions)
        inB = index in self.operation.indexAssignmentsB
        if inB and not inC: # is summation dimension
          self.totalFlops *= self.tensorA.dimensions[i].size
    return self.totalFlops

  def __str__(self):
    state = ""
    indexChars = "ijklmnopqrstuvwxyz"

    # device
    for device in self.deviceProfile.devices:
      state += device.name + "_"
    # operation type
    state += self.operation.type.__str__() + "_"
    # precisions
    state += self.tensorC.dataType.toChar()
    state += self.tensorA.dataType.toChar()
    state += self.tensorB.dataType.toChar()
    state += self.operation.alphaType.toChar()
    state += self.operation.betaType.toChar()
    # C
    state += "_C_"
    state += indexChars[0]
    state += str(self.tensorC.dimensions[0].stride) + "_" + str(self.tensorC.dimensions[0].size)
    for i in range(1, len(self.tensorC.dimensions)):
      state += "_"
      state += indexChars[i]
      state += str(self.tensorC.dimensions[i].stride) + "_" + str(self.tensorC.dimensions[i].size)
    # Sum
    state += "_Sum_"
    state += indexChars[len(self.tensorC.dimensions)]
    for j in range(0, len(self.tensorA.dimensions)):
      if self.operation.indexAssignmentsA[j] == 0 + len(self.tensorC.dimensions):
        state += str(self.tensorA.dimensions[j].size)
    for i in range(1, self.operation.numIndicesSummation):
      state += "_"
      state += indexChars[len(self.tensorC.dimensions)+i]
      for j in range( 0, len(self.tensorA.dimensions)):
        if self.operation.indexAssignmentsA[j] == i+len(self.tensorC.dimensions):
          state += str(self.tensorA.dimensions[j].size)
    # A
    state += "_A_"
    for i in range(0, len(self.tensorA.dimensions)):
      state += indexChars[self.operation.indexAssignmentsA[i]]
      state += str(self.tensorA.dimensions[i].stride)
      if i < len(self.tensorA.dimensions)-1:
        state += "_"
    # B
    state += "_B_";
    for i in range(0, len(self.tensorB.dimensions)):
      state += indexChars[self.operation.indexAssignmentsB[i]];
      state += str(self.tensorB.dimensions[i].stride)
      if i < len(self.tensorB.dimensions)-1:
        state += "_"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        self.tensorC, \
        self.tensorA, \
        self.tensorB, \
        self.operation, \
        self.deviceProfile, \
        )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Problem) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# BranchType - Enum
################################################################################
class BranchType:
  none = 0
  multiple = 1
  branched = 2

  def __init__(self, value):
    self.value = value

  def __str__(self):
    if self.value == self.none:
      return "none"
    elif self.value == self.multiple:
      return "multiple"
    elif self.value == self.branched:
      return "branched"
    else:
      return "ERROR"

  def getChar(self):
    if self.value == self.multiple:
      return "m"
    elif self.value == self.branched:
      return "b"
    else:
      return "x"

  def isNone(self):
    return self.value == self.none
  def isMultiple(self):
    return self.value == self.multiple
  def isBranched(self):
    return self.value == self.branched

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return (self.value)
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, BranchType) \
        and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Tile
################################################################################
class Tile:
  def __init__( self ):
    self.workGroup = [ -1, -1]
    self.microTile = [ -1, -1]
    self.branch = [ BranchType(-1), BranchType(-1)]

  def __str__(self):
    state = "[Tile; " + str(self.workGroup[0]) + "x" + str(self.workGroup[1])
    state += "; " + str(self.microTile[0]) + "x" + str(self.microTile[1])
    state += "; " + str(self.branch[0]) + "x" + str(self.branch[1])
    state += "]"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        self.workGroup[0], \
        self.workGroup[1], \
        self.microTile[0], \
        self.microTile[1], \
        self.branch[0], \
        self.branch[1], \
        )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Tile) \
        and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Kernel
################################################################################
class Kernel:
  def __init__( self ):
    self.dataTypeC = DataType(-1)
    self.dataTypeA = DataType(-1)
    self.dataTypeB = DataType(-1)
    self.dataTypeAlpha = DataType(-1)
    self.dataTypeBeta = DataType(-1)
    #self.operation = Operation()
    # Index Assignments
    self.indexOrderC = []
    self.indexOrderSummation = []
    self.indexAssignmentDim0 = -1
    self.indexAssignmentDim1 = -1
    self.unrollDimStride0 = -1
    self.unrollDimStride1 = -1
    self.unrollDimSize = -1
    self.unrollDimStrideGreaterThanTileDimStrideA = False
    self.unrollDimStrideLessThanTileDimStrideB = False
    self.transposeWorkGroupOrder = False

    # a kernel holds a copy of the problem so it can #define strides if necessary
    self.problem = Problem()

    # Tile
    self.tile = Tile()
    self.unrolls = []

    # global->local load strategy
    self.numLoadsParaA = -1
    self.loadSizeParaA = -1
    self.totalLoadSizeParaA = -1
    self.numLoadsPerpA = -1
    self.loadSizePerpA = -1
    self.totalLoadSizePerpA = -1
    self.numLoadsParaB = -1
    self.loadSizeParaB = -1
    self.totalLoadSizeParaB = -1
    self.numLoadsPerpB = -1
    self.loadSizePerpB = -1
    self.totalLoadSizePerpB = -1

    # Pre-Processor definition optimizations
    self.ppdOffsets = 0 # offsets are #defined and not arguments
    self.ppdLeadingStrides = 0 #leading strides are #defined and not arguments
    self.ppdAll = 0 #everything is #defined and not arguments

  # all loads using not all threads
  def loadRequiresFewerThreadsA(self):
    return self.tile.workGroup[0]*self.tile.workGroup[1] > self.loadSizeParaA * self.loadSizePerpA
  def loadRequiresFewerThreadsB(self):
    return self.tile.workGroup[0]*self.tile.workGroup[1] > self.loadSizeParaB * self.loadSizePerpB

  # last load (para or perp) requires additional guard b/c loading sub-load
  def lastLoadRequiresGuardParaA(self):
    return self.totalLoadSizeParaA < self.numLoadsParaA * self.loadSizeParaA
  def lastLoadRequiresGuardPerpA(self):
    return self.totalLoadSizePerpA < self.numLoadsPerpA * self.loadSizePerpA
  def lastLoadRequiresGuardParaB(self):
    return self.totalLoadSizeParaB < self.numLoadsParaB * self.loadSizeParaB
  def lastLoadRequiresGuardPerpB(self):
    return self.totalLoadSizePerpB < self.numLoadsPerpB * self.loadSizePerpB

  
  def useAlpha(self):
    return self.dataTypeAlpha.value != DataType.none
  def useBeta(self):
    return self.dataTypeBeta.value != DataType.none

  def __str__(self):
    state = "[Kernel; " + str(self.tile)
    state += "; " + str(self.dataTypeC)
    state += "; " + str(self.dataTypeA)
    state += "; " + str(self.dataTypeB)
    state += "; " + str(self.dataTypeAlpha)
    state += "; " + str(self.dataTypeBeta)
    state += "; " + str(self.indexOrderC)
    state += "; " + str(self.indexOrderSummation)
    state += "; " + str(self.indexAssignmentDim0)
    state += "; " + str(self.indexAssignmentDim1)
    state += "; " + str(self.tile)
    state += "; " + str(self.unrolls)
    state += "; " + str(self.numLoadsParaA)
    state += "; " + str(self.numLoadsParaB)
    state += "]"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        self.dataTypeC, \
        self.dataTypeA, \
        self.dataTypeB, \
        self.dataTypeAlpha, \
        self.dataTypeBeta, \
        tuple(self.indexOrderC), \
        tuple(self.indexOrderSummation), \
        self.indexAssignmentDim0, \
        self.indexAssignmentDim1, \
        self.unrollDimStrideGreaterThanTileDimStrideA, \
        self.unrollDimStrideLessThanTileDimStrideB, \
        self.tile, \
        tuple(self.unrolls), \
        self.ppdOffsets, \
        self.ppdLeadingStrides, \
        self.ppdAll, \
        self.numLoadsParaA, \
        self.numLoadsPerpA, \
        self.loadSizeParaA, \
        self.loadSizePerpA, \
        self.numLoadsParaB, \
        self.numLoadsPerpB, \
        self.loadSizeParaB, \
        self.loadSizePerpB \
        )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Kernel) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result


################################################################################
# Solution
################################################################################
class Solution:
  def __init__(self):
    # Solution Correctness Parameters
    # Kernels
    self.kernelGrid = [ -1, -1, -1 ]
    self.branch = [ BranchType(-1), BranchType(-1)]
    self.kernels = []

    # PreProcessor optimizations (#defining arguments)
    self.ppdOffsets = 0 # offsets are #defined and not arguments
    self.ppdLeadingStrides = 0 #leading strides are #defined and not arguments
    self.ppdAll = 0 #everything is #defined and not arguments

  def __str__(self):
    state = "[Solution"
    state += "; " + str(self.kernelGrid)
    state += "; " + str(self.kernels)
    state += "]"
    return state

  def __repr__(self):
    return self.__str__()

  def getAttributes(self):
    return ( \
        tuple(self.kernels), \
        self.kernelGrid[0], \
        self.kernelGrid[1], \
        self.branch[0], \
        self.branch[1], \
        self.ppdOffsets, \
        self.ppdLeadingStrides, \
        self.ppdAll )
  def __hash__(self):
    return hash(self.getAttributes())
  def __eq__(self, other):
    return isinstance(other, Solution) and self.getAttributes() == other.getAttributes()
  def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
      return result
    return not result

