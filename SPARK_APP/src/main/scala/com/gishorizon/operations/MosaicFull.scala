package com.gishorizon.operations

import geotrellis.layer.{Metadata, SpaceTimeKey, TemporalKey, TileLayerMetadata}
import geotrellis.raster.{MultibandTile, io => _, _}
import geotrellis.spark.ContextRDD
import org.apache.spark.rdd.RDD
import org.joda.time._

object MosaicFull {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], processOperation: ProcessOperation)
  : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
  = {

    var meta: TileLayerMetadata[SpaceTimeKey] = null
    val i = processOperation.inputs(0)
    val m = inputs(i.id).metadata
    meta = m
    val r1: RDD[(SpaceTimeKey, MultibandTile)] = inputs(i.id)
      .map{
        case (k, v) => {
          (SpaceTimeKey(k.spatialKey, TemporalKey(DateTime.now().getMillis)), v)
        }
      }
    r1.checkpoint()
    val inRdds: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(r1.reduceByKey(
      (t1: MultibandTile, t2: MultibandTile) => {
        val o = t1.merge(t2)
        print(DateTime.now() + "------MOSAIC TILE-----")
        o
      }
    ), m)

    inRdds.checkpoint()
    inRdds.cache()

  }


}
