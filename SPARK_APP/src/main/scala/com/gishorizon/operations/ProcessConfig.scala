package com.gishorizon.operations


class ProcessConfig {
  var inputs: Array[ProcessInput] = Array()
  var operations: Array[ProcessOperation] = Array()
  var output: ProcessOutput = new ProcessOutput()
}

class ProcessInput {
  var id: String = ""
  var tIndexes: Array[BigInt] = Array()
  var isTemporal: Boolean = false
  var aoiCode: String = ""
  var dsName: String = ""
  var band: Int = 0
}

class ProcessOutput {
  var id: String = ""
  var dsName: String = ""
}

class ProcessOperation {
  var id: String = ""
  var opType: String = ""
  var inputs: Array[ProcessInput] = Array()
  var output: ProcessOutput = new ProcessOutput()
  var params: String = ""
}