package com.gishorizon.operations

import breeze.linalg.diag
import com.gishorizon.Spark
import org.apache.spark.SparkContext
import org.apache.spark.ml.linalg
import org.apache.spark.mllib.linalg.DenseMatrix
import org.locationtech.jts.math.Matrix
import org.apache.spark.mllib.linalg.{Vector, Vectors}
import org.apache.spark.mllib.linalg.distributed._

object FPCA {

//  def main(args: Array[String]): Unit = {
//    implicit val sc: SparkContext = Spark.context
//    run(sc)
//  }

  def run(sc: SparkContext, matrix: BlockMatrix): (BlockMatrix, BlockMatrix) = { //v: Array[Vector]
    val N = matrix.numRows().toInt
    val L = 1
    val _N = matrix.numRows().toInt
    val _T = matrix.numCols().toInt
    val _t: List[Int] = (0 until _N).map{i=>{i.toInt}}.toList
    val scale = new CoordinateMatrix(
      sc.parallelize(_t)
        .map{
          i => {
            MatrixEntry(i, i, 1/Math.sqrt(_T))
          }
        },
      _N,
      _N
    ).toBlockMatrix()
    val svd = scale.multiply(matrix).transpose.toIndexedRowMatrix().computeSVD(L)
    val s = svd.s
    val Va = svd.V
    var Vl = Array[IndexedRow]()
    for (i <- 0 until N){
      Vl = Vl :+ IndexedRow(i, Vectors.dense(
        Va.toArray(L * i + 0),
      ))
    }
    val V = new IndexedRowMatrix(sc.parallelize(Vl), N, L)
    val S = new DenseMatrix(L, L, org.apache.spark.mllib.linalg.Matrices.diag(s).toArray)
    val Si = new DenseMatrix(L, L, org.apache.spark.mllib.linalg.Matrices.diag(
      Vectors.dense(s.toArray.map(e=>1/e))
    ).toArray)
    val scores = V.multiply(S)
    val t = V.multiply(Si).toBlockMatrix()
    val mt = matrix.transpose
    val components= mt.multiply(t)
    val FPCA = components.multiply(scores.toBlockMatrix().transpose )
    (components, FPCA)
  }

  def test(sc: SparkContext, arr: Array[IndexedRow]): (BlockMatrix, BlockMatrix) = {
    val matrix = new IndexedRowMatrix(sc.parallelize(arr)).toBlockMatrix().cache()
    val N = matrix.numRows().toInt
    val L = 1

    val _N = matrix.numRows().toInt
    val _T = matrix.numCols().toInt
    val _t: List[Int] = (0 until _N).map { i => {
      i.toInt
    }
    }.toList
    val scale = new CoordinateMatrix(
      sc.parallelize(_t)
        .map {
          i => {
            MatrixEntry(i, i, 1 / Math.sqrt(_T))
          }
        },
      _N,
      _N
    ).toBlockMatrix()
    val svd = scale.multiply(matrix).transpose.toIndexedRowMatrix().computeSVD(L)
    val s = svd.s
    val Va = svd.V
    var Vl = Array[IndexedRow]()
    for (i <- 0 until N) {
      Vl = Vl :+ IndexedRow(i, Vectors.dense(
        Va.toArray(L * i + 0),
        //        Va.toArray(L * i + 1)
      ))
    }
    val V = new IndexedRowMatrix(sc.parallelize(Vl), N, L)
    val S = new DenseMatrix(L, L, org.apache.spark.mllib.linalg.Matrices.diag(s).toArray)
    val Si = new DenseMatrix(L, L, org.apache.spark.mllib.linalg.Matrices.diag(
      Vectors.dense(s.toArray.map(e => 1 / e))
    ).toArray)
    val scores = V.multiply(S)
    val t = V.multiply(Si).toBlockMatrix()
    val mt = matrix.transpose
    val components = mt.multiply(t)
    val FPCA = components.multiply(scores.toBlockMatrix().transpose)
    (components, FPCA)
  }

}
