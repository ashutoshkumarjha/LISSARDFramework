package com.gishorizon.ingestion

import com.typesafe.config.ConfigFactory
import geotrellis.layer.{FloatingLayoutScheme, KeyBounds, SpaceTimeKey, SpatialKey, TemporalProjectedExtent, TileLayerMetadata, ZoomedLayoutScheme}
import geotrellis.proj4.WebMercator
import geotrellis.raster.MultibandTile
import geotrellis.raster.resample.{Bilinear, NearestNeighbor}
import geotrellis.spark.pyramid.Pyramid
import geotrellis.spark.reproject.TileRDDReprojectMethods
import geotrellis.spark.store.RasterReader
import geotrellis.spark.store.file.FileLayerWriter
import geotrellis.spark.{CollectTileLayerMetadata, ContextRDD, withTilerMethods}
import geotrellis.spark.store.hadoop.{HadoopGeoTiffRDD, HadoopLayerWriter}
import geotrellis.store.LayerId
import geotrellis.store.file.FileAttributeStore
import geotrellis.store.hadoop.HadoopAttributeStore
import geotrellis.store.index.ZCurveKeyIndexMethod
import geotrellis.vector.ProjectedExtent
import org.apache.commons.io.FilenameUtils
import org.apache.hadoop.conf.Configuration
import org.apache.hadoop.fs.Path
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

import java.time.{ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter

object IngestLandsat {
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

  private def log(msg: String): Unit = {
    println(f"[APP_LOG] $msg")
  }
}
