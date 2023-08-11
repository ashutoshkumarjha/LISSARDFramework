package com.gishorizon.operations

import geotrellis.layer.{Metadata, SpaceTimeKey, TileLayerMetadata}
import geotrellis.raster.{MultibandTile, io => _, _}
import geotrellis.spark.ContextRDD
import org.apache.spark.rdd.RDD

object LocalDif {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], operation: ProcessOperation): RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = {

    var inRdds: Array[RDD[(SpaceTimeKey, MultibandTile)]] = Array()
    var meta: TileLayerMetadata[SpaceTimeKey] = null

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
                  (v1 - v2)
                }
              })
          }
        )
      }
    }
    ContextRDD(or, meta)
  }




}
