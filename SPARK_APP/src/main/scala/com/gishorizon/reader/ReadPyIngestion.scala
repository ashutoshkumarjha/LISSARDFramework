package com.gishorizon.reader

import geotrellis.layer.{FloatingLayoutScheme, LayoutDefinition, Metadata, SpaceTimeKey, SpatialKey, TemporalProjectedExtent, TileLayerMetadata}
import geotrellis.raster.{MultibandTile, TileLayout}
import geotrellis.raster.geotiff.GeoTiffRasterSource
import geotrellis.raster.io.geotiff.reader.GeoTiffReader
import geotrellis.raster.resample.NearestNeighbor
import geotrellis.spark.store.hadoop.HadoopGeoTiffRDD
import geotrellis.spark.{CollectTileLayerMetadata, RasterSourceRDD, withTilerMethods}
import geotrellis.vector.ProjectedExtent
import org.apache.hadoop.fs.Path
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

import java.time.{Instant, ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter
import java.net.{HttpURLConnection, URL}
import scala.io.Source
import play.api.libs.json._

import java.io.File

object ReadPyIngestion {

  private val appBasePath = "C:/Users/ManiChan/Desktop/Project/spark-ee/geotrellis-app/"
  def run(sc: SparkContext): Unit = {

    val tIndex = 978413100L * 1000
    val indexStartTime = ZonedDateTime.parse("1990-01-01T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)))


    val url = new URL("http://localhost:8080/getDataForBbox/10?xmin=90.1474&ymax=25.7809&xmax=90.4697&ymin=25.2994&sensorName=Landsat8&tIndex=978413100")
    val connection = url.openConnection.asInstanceOf[HttpURLConnection]
    connection.setRequestMethod("GET")

    val responseCode = connection.getResponseCode
    if (responseCode == HttpURLConnection.HTTP_OK) {
      val inputStream = connection.getInputStream
      val responseBody = Source.fromInputStream(inputStream).mkString
      inputStream.close()

      val json: JsValue = Json.parse(responseBody)
      if(json.asInstanceOf[JsObject].value("error").toString()=="false"){
        val filePath = json.asInstanceOf[JsObject].value("data").toString()
        val relative = new File(appBasePath).toURI.relativize(new File(filePath).toURI).getPath
//        val sRdd = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
//          path = new Path(relative),
//          uriToKey = {
//            case (uri, pExtent) => {
//              val timestamp: Instant = Instant.ofEpochMilli(indexStartTime.toInstant.toEpochMilli + tIndex)
//              TemporalProjectedExtent(pExtent, ZonedDateTime.ofInstant(timestamp, ZoneOffset.ofHoursMinutes(0, 0)))
//            }
//          },
//          options = HadoopGeoTiffRDD.Options.DEFAULT
//        )
        val rasterSource = GeoTiffReader.readMultiband(filePath)
        val rowRdd: RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]] = RasterSourceRDD.spatial(
          GeoTiffRasterSource(filePath),
          LayoutDefinition(
            rasterSource.extent,
            TileLayout(rasterSource.tile.cols, rasterSource.tile.rows, rasterSource.tile.cols, rasterSource.tile.rows)
          )
        )(sc)

        println(rowRdd)

      }else{

      }
      // Process the JSON
    } else {
      // Handle error
    }

    connection.disconnect()

////    val aoiExtent = Array(67.5, 0, 112.5, 41)
//    val zoom = 9
//    val tIndex = 889417419
//    val indexStartTime = ZonedDateTime.parse("1990-01-01T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)))
//    val zoomRes = Map(
//      4 -> Array(22.5, 19.03685253618195),
//      5 -> Array(11.25, 10.009116704586791),
//      6 -> Array(5.625, 4.8930364536509146),
//      7 -> Array(2.8125, 2.4761037785744016),
//      8 -> Array(1.40625, 1.245254898588719),
//      9 -> Array(0.703125, 0.6244022994137062),
//      10 -> Array(0.3515625, 0.3126415161489824),
//      11 -> Array(0.17578125, 0.15643042465561763),
//      12 -> Array(0.087890625, 0.07824257542153745),
//    )
//    val zoomExtent = Map(
//      4 -> Array(67.5, 0.0, 112.5, 40.97989806962013),
//      5 -> Array(67.5, 0.0, 101.25, 40.97989806962013),
//      6 -> Array(67.5, 5.615985819155334, 101.25, 40.97989806962013),
//      7 -> Array(67.5, 5.615985819155334, 98.4375, 38.8225909761771),
//      8 -> Array(67.5, 7.0136679275666305, 98.4375, 37.718590325588146),
//      9 -> Array(67.5, 7.7109916554332205, 97.734375, 37.160316546736766),
//      10 -> Array(67.8515625, 8.059229627200187, 97.734375, 37.160316546736766),
//      11 -> Array(68.02734375, 8.059229627200187, 97.55859375, 37.160316546736766),
//      12 -> Array(68.02734375, 8.059229627200187, 97.470703125, 37.090239803072066),
//    )
//
//    val aoiExtent = zoomExtent(zoom)
//
//    val inExtent = Array(90.8845, 25.8404, 91.1870, 26.2323)
//    val resY = zoomRes(zoom)(1)
//    val resX = zoomRes(zoom)(0)
//
//    val xCount = math.ceil((aoiExtent(2) - aoiExtent(0))/resX).toInt
//    val yCount = math.ceil((aoiExtent(3) - aoiExtent(1)) / resY).toInt
//
//    val xStart = Math.ceil((inExtent(0) - aoiExtent(0))/resX).toInt
//    val yStart = Math.ceil((inExtent(1) - aoiExtent(1)) / resY).toInt
//    val xEnd = Math.ceil((inExtent(2) - aoiExtent(0)) / resX).toInt
//    val yEnd = Math.ceil((inExtent(3) - aoiExtent(1)) / resY).toInt
//
//    var rdds = Array[RDD[(TemporalProjectedExtent, MultibandTile)]]()
//    for (x <- xStart to xEnd){
//      for (y <- yStart to yEnd) {
//        val filePath = dataPath + "/" + zoom.toString + "/" + x.toString + "/" + y.toString + "/" + tIndex.toString + ".tif"
//        val sRdd = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
//          path = new Path(filePath),
//          uriToKey = {
//            case (uri, pExtent) => {
//              val timestamp: Instant = Instant.ofEpochMilli(indexStartTime.toInstant.toEpochMilli + tIndex.toLong)
//              TemporalProjectedExtent(pExtent, ZonedDateTime.ofInstant(timestamp, ZoneOffset.ofHoursMinutes(0, 0)))
//            }
//          },
//          options = HadoopGeoTiffRDD.Options.DEFAULT
//        )
//        rdds = rdds :+ sRdd
//      }
//    }
//    rdds.head.collect()
//    println(xStart, yStart, xEnd, yEnd)

  }
}
