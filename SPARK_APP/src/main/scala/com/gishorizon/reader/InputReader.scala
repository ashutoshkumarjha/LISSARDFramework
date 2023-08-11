package com.gishorizon.reader

import com.gishorizon.operations.{FpcaTemporal, ProcessInput, ProcessOperation}
import com.gishorizon.{DataConfigs, Logger, RddUtils, Spark}
import geotrellis.layer.{Metadata, SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.raster.MultibandTile
import geotrellis.spark.ContextRDD
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import play.api.libs.json._
import geotrellis.raster.io.geotiff

import scala.collection.mutable.Map
import java.sql.{Connection, DriverManager}
import java.time.{Instant, ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter
import scala.collection.{immutable, mutable}


object InputReader {

  private def getConnection: Connection = {
    classOf[org.postgresql.Driver]
    val connStr = "jdbc:postgresql://localhost:5432/project_master?user=postgres&password=manichan"
    val conn = DriverManager.getConnection(connStr)
    conn
  }

  private def getAoi(aoiCode: String): Unit = {
    val conn = getConnection
    val st = conn.createStatement()
    val resultSet = st.executeQuery("select aoi_code, st_asgeojson(geom) as geom from user_aoi where aoi_code='"+aoiCode+"';")
    while (resultSet.next()) {
      val aoiCode = resultSet.getString("aoi_code")
      val geom = resultSet.getString("geom")
      println(aoiCode, geom)
    }
  }



  private def getInputRdd(sc: SparkContext, processInput: ProcessInput): RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]] = {
    val data = HttpUtils.getRequestSync(s"${DataConfigs.DATA_HOST}/getDataRefForAoi/?sensorName=${processInput.dsName}&tIndex=${processInput.tIndexes(0)}&level=12&aoiCode=${processInput.aoiCode}")
    val filePaths = data.asInstanceOf[JsObject].value("data").asInstanceOf[JsArray]
    var rdds: Array[RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]]] = Array()
    for (i <- filePaths.value.indices) {
      val filePath = filePaths(i).asInstanceOf[JsString].value
      var rdd = RddUtils.getMultiTiledRDDWithMeta(sc, filePath, 256)
      rdds = rdds :+ rdd
    }
    RddUtils.mergeRdds(rdds)
  }

//  private def getInputRdd1Temporal(sc: SparkContext, processInput: ProcessInput): RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = {
//    val data = HttpUtils.getRequestSync(s"${DataConfigs.DATA_HOST}/getDataRefForAoi/?sensorName=${processInput.dsName}&tIndex=${processInput.tIndexes(0)}&level=12&aoiCode=${processInput.aoiCode}")
//    val filePaths = data.asInstanceOf[JsObject].value("data").asInstanceOf[JsArray]
//    var rdds: Array[RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Array()
//    for (i <- filePaths.value.indices) {
//      val filePath = filePaths(i).asInstanceOf[JsString].value
//      val tIndex = filePath.split("/").last.split(".tif").head.toInt
//      val sTs = ZonedDateTime.parse(f"1990-01-01T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0))).toInstant.toEpochMilli
//      val dt = ZonedDateTime.ofInstant(
//        Instant.ofEpochMilli((sTs + tIndex * 1000))
//        , DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)).getZone
//      )
//      var rdd = RddUtils.getMultiTiledTemporalRDDWithMeta(sc, filePath, 256, dt)
//      rdds = rdds :+ rdd
//    }
//    RddUtils.mergeTemporalRdds(rdds)
//  }

  private def getInputRddTemporal(sc: SparkContext, processInput: ProcessInput)
  : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
  = {
    val data = HttpUtils.getRequestSync(s"${DataConfigs.DATA_HOST}/getDataRefsForAoi/?sensorName=${processInput.dsName}&tIndexes=${processInput.tIndexes.mkString("", ",", "")}&level=8&aoiCode=${processInput.aoiCode}")
    val filePaths = data.asInstanceOf[JsObject].value("data").asInstanceOf[JsArray]
//    var rdds: Array[RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Array()
    val paths: Array[String] = filePaths.value.map{
      v=>{
        DataConfigs.TILE_PATH + v.asInstanceOf[JsString].value
      }
    }.toArray[String]
    val rdd = RddUtils.getMultiTiledTemporalRDDWithMeta(sc, paths, 256)
    rdd.checkpoint()
    rdd.cache()
//    for (i <- filePaths.value.indices) {
//      val filePath = DataConfigs.TILE_PATH + filePaths(i).asInstanceOf[JsString].value//.replace("/", "_").replace("Landsat_OLI_", "Landsat_OLI/").replace("LISS3_", "LISS3/")
//      Logger.log("Reading " + filePath)
//      val tIndex = filePath.split("/").last.split(".tif").head.toInt
//      val sTs = ZonedDateTime.parse(f"1990-01-01T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0))).toInstant.toEpochMilli
//      val dt = ZonedDateTime.ofInstant(
//        Instant.ofEpochMilli((sTs + tIndex * 1000L))
//        , DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)).getZone
//      )
//      val rdd = RddUtils.getMultiTiledTemporalRDDWithMeta(sc, filePath, 256, dt)
//      rdd.checkpoint()
//      rdds = rdds :+ rdd
//    }
//    val merged = RddUtils.mergeTemporalRdds(rdds)
//    Logger.log("Merged: " + processInput.id)
//    merged
  }

  def getInputs(sc: SparkContext, inputs: Array[ProcessInput]): mutable.Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = {
    var rddMap = mutable.Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]]()
    for(input <- inputs){
      var rdd: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = getInputRddTemporal(sc, input)
      rdd = rdd.cache()
      rdd.checkpoint()
      rddMap += (
        input.id -> rdd
      )
    }
    rddMap
  }

}
