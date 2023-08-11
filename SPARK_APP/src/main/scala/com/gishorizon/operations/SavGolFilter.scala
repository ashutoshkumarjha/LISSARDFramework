package com.gishorizon.operations

import breeze.linalg.{DenseMatrix, inv}
import com.gishorizon.RddUtils._
import com.gishorizon.Spark
import geotrellis.layer.{Metadata, SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.raster.io.geotiff.{GeoTiff, GeoTiffOptions}
import geotrellis.raster.{ArrayMultibandTile, ArrayTile, MultibandTile, Raster, Tile}
import geotrellis.spark.ContextRDD
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import geotrellis.raster.io.geotiff.writer.GeoTiffWriter
import geotrellis.raster._
import geotrellis.spark._

object SavGolFilter {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], operation: ProcessOperation): RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = {

    val w = operation.params.split("#")(1).toInt
    val p = operation.params.split("#")(0).toInt

    val in1: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = inputs(operation.inputs(0).id)
    val rdd = in1
    runForRdd(rdd, rdd.metadata, w, p)
  }

  private def runForRdd(rdd: RDD[(SpaceTimeKey, MultibandTile)], meta: TileLayerMetadata[SpaceTimeKey], w: Int, p: Int): RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = {
    val tileSize = 256
    val result: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(rdd.map {
      case (k, t) =>
        var _tv = Array[Array[Int]]()
        for(b <- 0 until t.bandCount){
          _tv = _tv :+ t.band(b).toArray()
        }
        val tv = _tv.head.indices.map(i => _tv.map(_(i))).toArray
        val bandCount = t.bandCount
        var resultTiles = Array[Tile]()
        for (b <- 0 until bandCount) {
          resultTiles = resultTiles :+ ArrayTile(tv.map {
            v => {
              solve(v.map(e => e.toDouble).map(e=>{
                if(e < 0){
                  Double.NaN
                }else{
                  e
                }
              }), w, p)
              //TODO: Calculate least sq error and apply optimum params: Least square error from original values: p = 2-4, w = 3-5
//              var wParam = 3
//              var pParam = 2
//              var err = Double.MaxValue
//              val _a = v
//              var outAr = Array[Double]()
//              for(w <- 3 to 5){
//                for(p <- 2 to 4){
//                  if(w>p){
//                    val rY = solve(_a.map(e => e.toDouble), w, p)
//                    val _err = getLeaseSquareError(_a.map(e=>e), rY)
//                    if(_err<err){
//                      wParam = w
//                      pParam = p
//                      err = _err
//                      outAr = rY
//                    }
//                  }
//                }
//              }
//              outAr
            }
          }.map {
            v => {
              v(b)
            }
          }, tileSize, tileSize)
        }
        val mTile: MultibandTile = new ArrayMultibandTile(resultTiles)
        (
          k, mTile
        )
    }, meta)
    result
//    println("------------Saving----------")
//    val rasterTile: Raster[MultibandTile] =  result.stitch()
//    GeoTiffWriter.write(GeoTiff(rasterTile, meta.crs), "data/result.tif")
//    println("------------Done----------")
  }

  def getLeaseSquareError(x: Array[Double], y: Array[Double]): Double = {
    var er = 0.0
    for(i <- y.indices){
      er = er + Math.pow(y(i)-x(i), 2)
    }
    er
  }

  def getX(w: Int, p: Int, values: Array[Double]): DenseMatrix[Double] = {
    var matVals = Array[Double]()
    for(i <- 0 to p){
      for(j <- 0 until w){
        matVals = matVals :+ Math.pow(values(j), i)
      }
    }
    val X = new DenseMatrix(w, p+1, matVals)
    X
  }

  def getHFromX(X: DenseMatrix[Double]): DenseMatrix[Double] = {
    inv( X.t * X ) * X.t
  }

  def getCoeff(H: DenseMatrix[Double], values: Array[Double], w: Int, p: Int): Array[Double] = {
    val Y = new DenseMatrix(w, 1, values)
    (H * Y).toArray
  }

  def solve(_y: Array[Double], w: Int, p: Int): Array[Double] = {
    if(_y.forall(_p => _p.isNaN)){
      return _y
    }
    val y = _y.map(e=>{
      if(e>15000) _y.min else e
    })
    val hw: Int = w/2
    val xVals = y.indices.map(e => e.toDouble).toArray
    var outY: Array[Double] = y.slice(0, hw)
    for (i <- 0 until y.length - 2*hw){
      val _y = y.slice(i, i + w)
      val X = getX(w, p, xVals.slice(i, i + w))
      val H = getHFromX(X)
      val coeff = getCoeff(H, _y, w, p)
      var yCalc: Double = 0
      for (c <- 0 to p) {
        val _x = xVals(i+hw)
        yCalc = yCalc + coeff(c) * Math.pow(_x, c)
      }
      outY = outY :+ yCalc

    }
    outY  = outY ++ y.slice(y.length-hw, y.length)
//    println(outY.mkString("Array(", ", ", ")"))
    outY
  }

}
