package com.gishorizon.operations

import geotrellis.layer.{Metadata, SpaceTimeKey, TemporalKey, TileLayerMetadata}
import geotrellis.raster.{MultibandTile, Tile, io => _, _}
import geotrellis.spark.ContextRDD
import org.apache.spark.rdd.RDD
import org.joda.time._

object BandSelector {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], processOperation: ProcessOperation)
  : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
  = {
    val selbandNo = processOperation.params.split("#").head.toInt
    val i = processOperation.inputs(0)
    val meta = inputs(i.id).metadata
    val inRdds: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(inputs(i.id)
      .map{case(k, t)=>{
        val mt: MultibandTile = ArrayMultibandTile(t.band(selbandNo))
        (k, mt)
    }}, meta)
    inRdds
  }


}
