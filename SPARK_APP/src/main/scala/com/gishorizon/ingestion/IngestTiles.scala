package com.gishorizon.ingestion

import com.typesafe.config.ConfigFactory
import geotrellis.layer.{FloatingLayoutScheme, KeyBounds, Metadata, SpaceTimeKey, SpatialKey, TemporalProjectedExtent, TileLayerMetadata, ZoomedLayoutScheme}
import geotrellis.proj4.{CRS, WebMercator}
import geotrellis.raster.{MultibandTile, Tile}
import geotrellis.raster.resample.{Bilinear, NearestNeighbor}
import geotrellis.spark.pyramid.Pyramid
import geotrellis.spark.reproject.TileRDDReprojectMethods
import geotrellis.spark.store.RasterReader
import geotrellis.spark.store.file.{FileLayerReader, FileLayerWriter}
import geotrellis.spark.store.hadoop.{HadoopGeoTiffRDD, HadoopLayerWriter}
import geotrellis.spark.{CollectTileLayerMetadata, ContextRDD, withTilerMethods}
import geotrellis.store.{AttributeStore, Between, Intersects, LayerId}
import geotrellis.store.file.FileAttributeStore
import geotrellis.store.hadoop.HadoopAttributeStore
import geotrellis.store.index.ZCurveKeyIndexMethod
import geotrellis.vector.{Extent, ProjectedExtent}
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.Path
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

import java.time.format.DateTimeFormatter
import java.time.{ZoneOffset, ZonedDateTime}
import com.gishorizon.Spark
import com.gishorizon.operations.{NDI, ProcessInput, ProcessOperation}
import geotrellis.store.s3.S3AttributeStore
import org.joda.time.DateTime
object IngestTiles {
  private val appConf = ConfigFactory.load()
  val layerName = "Landsat8"

  def run(sc: SparkContext, srcPath: String, dataTime: String, catalogType: String): Unit = {
    val sRdd = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
      path = new Path(srcPath),
      uriToKey = {
        case (uri, pExtent) => {
          TemporalProjectedExtent(pExtent, ZonedDateTime.parse(dataTime, DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0))))
        }
      },
      options = HadoopGeoTiffRDD.Options.DEFAULT
    )(sc, RasterReader.multibandGeoTiffReader)
    val (zoom, meta) = CollectTileLayerMetadata.fromRDD[TemporalProjectedExtent, MultibandTile, SpaceTimeKey](sRdd, FloatingLayoutScheme(256))

    val tiled: RDD[(SpaceTimeKey, MultibandTile)] = sRdd.tileToLayout(
      meta,
      NearestNeighbor
    )
      .repartition(64)
    val layoutScheme = ZoomedLayoutScheme(WebMercator, tileSize = 256)
    val (_zoom, _rep) = new TileRDDReprojectMethods(ContextRDD(tiled, meta)).reproject(layoutScheme, Bilinear)

    val minK: SpatialKey = _rep.metadata.pointToKey(7425024.704, 4536549.739) //meta.bounds.get.minKey
    val maxK: SpatialKey = _rep.metadata.pointToKey(10925898.114, 821573.326) // meta.bounds.get.maxKey
    val updatedMeta = _rep.metadata.updateBounds(KeyBounds(new SpaceTimeKey(minK.col, minK.row, 1262284200000L), new SpaceTimeKey(maxK.col, maxK.row, 1735669800000L)))
    val _rdd = ContextRDD(_rep, updatedMeta)

    if (catalogType=="file"){
      val fileCatalogPath = appConf.getString("FILE_CATALOG_PATH") + layerName
      val attributeStore = FileAttributeStore(fileCatalogPath)
      val writer = FileLayerWriter(attributeStore)

      Pyramid.upLevels(_rdd, layoutScheme, _zoom, NearestNeighbor){
        (rdd, zoom) => {
          log(f"Saving zoom $zoom")
          if(attributeStore.layerExists(layerId = LayerId(layerName, zoom))){
            writer.overwrite[
              SpaceTimeKey,
              MultibandTile,
              TileLayerMetadata[SpaceTimeKey]
            ](LayerId(layerName, zoom), rdd)
          }else{
            writer.write(LayerId(layerName, zoom), rdd, ZCurveKeyIndexMethod.bySeconds(10))
          }
          log(f"Saved zoom $zoom")
        }
      }
      log(f"Saved [$layerName] $srcPath")
      log("-------RDD created-------")
    }else if (catalogType == "hdfs") {
      val fileCatalogPath = appConf.getString("HDFS_CATALOG_PATH") + layerName
      val configuration: Configuration = new Configuration()
      configuration.set("fs.permissions.enabled", "false")
      val attributeStore = HadoopAttributeStore(new Path(fileCatalogPath), configuration)
      val writer = new HadoopLayerWriter(new Path(fileCatalogPath), attributeStore);

      Pyramid.upLevels(_rdd, layoutScheme, _zoom, NearestNeighbor) {
        (rdd, zoom) => {
          log(f"Saving zoom $zoom")
          if (attributeStore.layerExists(layerId = LayerId(layerName, zoom))) {
            writer.overwrite[
              SpaceTimeKey,
              MultibandTile,
              TileLayerMetadata[SpaceTimeKey]
            ](LayerId(layerName, zoom), rdd)
          } else {
            writer.write(LayerId(layerName, zoom), rdd, ZCurveKeyIndexMethod.bySeconds(10))
          }
          log(f"Saved zoom $zoom")
        }
      }
      log(f"Saved [$layerName] $srcPath")
      log("-------RDD created-------")
    }else{
      throw new Throwable("Error: Unsupported data catalog type")
    }
  }

  private def read(implicit sc: SparkContext, startDt: String, endDt: String): Unit = {
    val fileCatalogPath = appConf.getString("FILE_CATALOG_PATH") + layerName
    val attributeStore = FileAttributeStore(fileCatalogPath)
    val reader = FileLayerReader(attributeStore)
    val layerIds = reader.attributeStore.layerIds.filter { id => id.name == layerName }
    val zooms = layerIds.map {
      _.zoom
    }
    val maxZoom = zooms.max
    val stDt = ZonedDateTime.parse(startDt, DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30)))
    val edDt = ZonedDateTime.parse(endDt, DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30)))
    val extent = ProjectedExtent(new Extent(79.1189, 30.0055, 79.3222, 30.3047), CRS.fromEpsgCode(4326))
    val t = extent.reproject(CRS.fromString("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs "))

    println(DateTime.now() + "----------------QUERY-----------------")
    val queryResult = reader
        .query[SpaceTimeKey, MultibandTile, TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, 8))
        .where(
          Intersects(
            extent.reproject(CRS.fromString("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs "))
          )
        )
        .where(
          Between(
            stDt, edDt
          )
        )
        .result
    queryResult.cache()
    queryResult.checkpoint()
    println(queryResult)
    println(DateTime.now() + "---------------QUERY--------------")
    val input1 = new ProcessInput()
    input1.id = "I1"
    val input2 = new ProcessInput()
    input2.id = "I2"

    val operation = new ProcessOperation()
    operation.id = "op_ndi"
    operation.inputs = Array(input1, input2)
    operation.params = "I1:3#I2:4"
    val i: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Map(
      "I1" -> queryResult,
      "I2" -> queryResult
    )
    queryResult.map{
      case (k, v) => {
        v.combine(1, 3){
          (v, v2)=>{
            v + v2
          }
        }
      }
    }.collect()
//    println(DateTime.now() + "----------------START-----------------")
//    NDI.runProcess(i, operation).collect()
//    println(DateTime.now() + "----------------END-----------------")
  }

  private def log(msg: String): Unit = {
    println(f"[APP_LOG] $msg")
  }

  def main(args: Array[String]): Unit = {
//    IngestTiles.run(
//      Spark.context, "/mnt/data/data_dir/raw/LC08_L2SP_144039_20191226_20200824_02_T1_SR/LC08_L2SP_144039_20191226_20200824_02_T1_SR.tif", "2019-12-26T00:00:00Z", "file"
//    )
    IngestTiles.read(Spark.context, "2019-12-24T00:00:00Z", "2019-12-27T00:00:00Z")
  }
}
