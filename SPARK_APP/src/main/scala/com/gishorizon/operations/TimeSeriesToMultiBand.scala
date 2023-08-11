package com.gishorizon.operations

import geotrellis.layer.{Metadata, SpaceTimeKey, TileLayerMetadata}
import geotrellis.raster.{MultibandTile, io => _, _}
import geotrellis.spark.ContextRDD
import org.apache.spark.rdd.RDD

object TimeSeriesToMultiBand {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], processOperation: ProcessOperation)
  : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
  = {
    val i = processOperation.inputs(0)
    val meta = inputs(i.id).metadata
    val inRdds: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(inputs(i.id)
      .map {
        case (k, v) => {
          (k.spatialKey, v)
        }
      }.reduceByKey(
      (t1: MultibandTile, t2: MultibandTile) => {
        var tils: Array[Tile] = Array()
        for (i <- 0 until t1.bandCount) {
          tils = tils :+ t1.band(i)
        }
        for (i <- 0 until t2.bandCount) {
          tils = tils :+ t2.band(i)
        }
        val r: MultibandTile = ArrayMultibandTile(tils)
        r
      }
    ).map{case (a,b)=>{
      (SpaceTimeKey(a, meta.bounds.get.maxKey.time), b)
    }}, meta)
    inRdds
  }


}
