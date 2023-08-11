package com.gishorizon.operations

import geotrellis.layer.{Bounds, Metadata, SpaceTimeKey, SpatialKey, TemporalKey, TileLayerMetadata}
import geotrellis.raster.{ArrayTile, MultibandTile, Raster, Tile}
import geotrellis.spark.{ContextRDD, MultibandTileLayerRDD, RasterSourceRDD, RasterSummary, TileLayerRDD, withTilerMethods, _}
import geotrellis.spark.store.file.FileLayerReader
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.store.{Intersects, LayerId}
import geotrellis.store.file.FileAttributeStore
import com.gishorizon.RddUtils.singleTiffTimeSeriesRdd
import com.gishorizon.{Logger, RddUtils, Spark}
import org.apache.spark.SparkContext
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.linalg.distributed._
import org.apache.spark.rdd.RDD
import geotrellis.raster.io.geotiff._
import geotrellis.raster.{io => _, _}
import geotrellis.spark.stitch._
import org.joda.time.Interval

import java.awt.Color
import java.awt.image.BufferedImage
import java.io.File
import java.time.{ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter
import javax.imageio.ImageIO
import scala.Double.NaN
import org.joda.time._

object ChangeDetection {

  def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], processOperation: ProcessOperation)
  : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
  = {

    var in1: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = inputs(processOperation.inputs(0).id)
    var in2: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = inputs(processOperation.inputs(1).id)
    val rdd: RDD[(SpatialKey, MultibandTile)] = in1.merge(in2).map {
      case (k, v) => {
        (k.spatialKey, v)
      }
    }.reduceByKey(
      (t1: MultibandTile, t2: MultibandTile) => {
        val mt = MultibandTile(
          t1.band(0).convert(CellType.fromName("float64")).combineDouble(t2.band(0).convert(CellType.fromName("float64"))) {
            (v1, v2) => {
              (v1 - v2)
            }
          }
        )
        mt
      }
    )
    ContextRDD(
      rdd
        .map {
          case (k, t) => {
            Logger.log("CD Done")
            (SpaceTimeKey(k, in1.metadata.bounds.get.maxKey.time), t)
          }
        },
      in1.metadata
    )
  }


  def write(tiles: MultibandTileLayerRDD[SpatialKey], path: String): Unit = {
    GeoTiff(tiles.stitch().tile, tiles.metadata.extent, tiles.metadata.crs).write(path)
  }

}
