package com.gishorizon.operations

import com.gishorizon.RddUtils.mergeRdds
import geotrellis.layer.{LayoutDefinition, Metadata, SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.spark.{ContextRDD, withTileRDDMergeMethods}
import geotrellis.vector.ProjectedExtent
import org.apache.spark.rdd.RDD
import com.gishorizon.Spark
import com.gishorizon.reader.{HttpUtils, InputReader}
import geotrellis.layer.{LayoutDefinition, Metadata, SpatialKey, TileLayerMetadata}
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.raster.resample.NearestNeighbor
import geotrellis.raster.{MultibandTile, Raster, Tile}
import org.apache.spark.rdd.RDD
import geotrellis.raster.{io => _, _}
import geotrellis.spark._
import geotrellis.spark.stitch._

object LocalAvg {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], operation: ProcessOperation): RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = {

    var inRdds: Array[RDD[(SpaceTimeKey, MultibandTile)]] = Array()
    var meta: TileLayerMetadata[SpaceTimeKey] = null
    val iCount = operation.inputs.length

    for(i <- operation.inputs.indices){
      val op = operation.inputs(i)
      val rdd = inputs(op.id)
      val bid = op.band
      val r: RDD[(SpaceTimeKey, MultibandTile)] = rdd.map {
        case (k: SpaceTimeKey, mt: MultibandTile) => {
          val _mt: MultibandTile = ArrayMultibandTile(mt.band(bid))
          (k, _mt)
        }
      }
      meta = rdd.metadata
      inRdds = inRdds :+ r
    }
    val or: RDD[(SpaceTimeKey, MultibandTile)] = inRdds.reduce{
      (rdd1, rdd2) => {
        rdd1.++(rdd2).reduceByKey(
          (t1: MultibandTile, t2: MultibandTile) => {
            ArrayMultibandTile(t1.band(0).convert(CellType.fromName("float32"))
              .combineDouble(t2.band(0).convert(CellType.fromName("float32"))) {
                (v1, v2) => {
                  v1 + v2
                }
              })
          }
        )
      }
    }.map{
      case (k, mt) => {
        (k, mt.mapDouble(0){
          (v)=>{
            v/iCount
          }
        })
      }
    }
//      .map{
//      case(k, t) => {
//        val mt: MultibandTile = new ArrayMultibandTile(Array(t))
//        (k, mt)
//      }
//    }
    ContextRDD(or, meta)
  }




}
