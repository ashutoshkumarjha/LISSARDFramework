package com.gishorizon

//some utility functions to write an RDD to a Geotiff, for debugging purposes.
//https://proba-v-mep.esa.int/blog/foss4g-demo-timeseries-analysis-geotrellis
import geotrellis.layer.{Metadata, SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.raster.io.geotiff._
import geotrellis.raster.{io => _, _}
import geotrellis.spark._
import geotrellis.spark.stitch._
import org.apache.spark.rdd.RDD
class FileUtility {


  def toFile(filename:String,rdd:TileLayerRDD[SpatialKey] ) =
  {
    val raster: Raster[Tile] = rdd.stitch
    GeoTiff(raster, rdd.metadata.crs).write(filename)
  }

  def toFile2(filename:String,rdd:RDD[(SpatialKey,Tile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]) =
  {
    val raster: Raster[Tile] = rdd.stitch
    GeoTiff(raster, rdd.metadata.crs).write(filename)
  }
}
