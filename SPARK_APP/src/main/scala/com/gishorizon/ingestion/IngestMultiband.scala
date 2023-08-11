package com.gishorizon.ingestion

import com.gishorizon.Spark
import com.gishorizon.operations.FPCA
import geotrellis.layer.{Bounds, FloatingLayoutScheme, KeyBounds, SpaceTimeKey, SpatialKey, TemporalProjectedExtent, TileLayerMetadata, ZoomedLayoutScheme}
import geotrellis.proj4.WebMercator
import geotrellis.raster.{MultibandTile, Tile}
import geotrellis.raster.resample.{Bilinear, NearestNeighbor}
import geotrellis.spark.pyramid.Pyramid
import geotrellis.spark.reproject.TileRDDReprojectMethods
import geotrellis.spark.store.file.{FileLayerReader, FileLayerWriter}
import geotrellis.spark.store.hadoop.HadoopGeoTiffRDD
import geotrellis.spark.{CollectTileLayerMetadata, ContextRDD, withTilerMethods}
import geotrellis.store.{Between, Intersects, LayerId}
import geotrellis.store.file.FileAttributeStore
import geotrellis.store.index.ZCurveKeyIndexMethod
import geotrellis.vector.ProjectedExtent
import org.apache.commons.io.FilenameUtils
import org.apache.hadoop.fs.Path
import org.apache.spark.SparkContext
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.linalg.distributed.{IndexedRow, IndexedRowMatrix}
import org.apache.spark.rdd.RDD

import java.awt.Color
import java.awt.image.BufferedImage
import java.io.File
import java.time.format.DateTimeFormatter
import java.time.{Instant, ZoneOffset, ZonedDateTime}
import javax.imageio.ImageIO

object IngestMultiband {
//  def main(args: Array[String]): Unit = {
//    val filePath = "data/in/liss3/12-05-2019.tif"
//    val outputCatalogPath = "data/out/multiTiffCombinedTsRdd"
//    val layerName = "multiTiffCombinedTsRdd"
//
//    implicit val sc: SparkContext = Spark.context
//
//    val attributeStore = FileAttributeStore(outputCatalogPath)
//
//    val reader = FileLayerReader(attributeStore)
//    val layerIds = reader.attributeStore.layerIds.filter { id => id.name == layerName }
//    val zooms = layerIds.map {
//      _.zoom
//    }
//    val maxZoom = zooms.max
////    val key = new SpaceTimeKey(5873, 3371, 1522521000000L)
//    val key = new SpaceTimeKey(0, 0, 1522521000000L)
////    val rdd = reader.read[SpaceTimeKey, MultibandTile, TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, 13)).first()
//    val timeFrom = ZonedDateTime.ofInstant(
//      Instant.ofEpochMilli(1302284200000L),
//      DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30)).getZone
//    )//ZonedDateTime.parse(f"2020-01-01T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30)))
//    val timeTo = ZonedDateTime.ofInstant(
//      Instant.ofEpochMilli(1495669800000L),
//      DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30)).getZone
//    )
//
//    val queryResult = reader
////      .read[SpaceTimeKey, Tile, TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, 0))
//      .query[SpaceTimeKey, Tile, TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, 0))
//      .where(
//        Intersects(
//          key.spatialKey.extent(attributeStore.readMetadata[TileLayerMetadata[SpaceTimeKey]](LayerId(layerName, 0)))
//        )
//      )
////      .where(
////        Between(
////          timeFrom, timeTo
////        )
////      )
//      .result
////    val q = queryResult
////      .map{
////        case (k, t) => {
////          (k.spatialKey, t)
////        }
////      }
////      .aggregateByKey(Array[Array[Int]]())({
////        (a, b)=>{
////          Array.concat(a, b.toArray())
////        }
////      }, {
////        (a, b) => {
////          Array.concat(a, b)
////        }
////      })
////      .collect()
//    /*
//    * _rdd.mapPartitions(
//      p =>
//        p.flatMap(mt => {
//          mt._2.bands.toList.take(36).zipWithIndex.map(t => {
//            val dt = new DateTime(mt._1.instant).plusDays(t._2 * 10)
//            (new SpaceTimeKey(mt._1.col, mt._1.row, dt.getMillis), t._1)
//          })
//        })
//    )
//    * */
////    val t = queryResult.mapPartitions(
////      p =>
////        p.map{
////          case (k, t) => {
////            (k.spatialKey, t)
////          }
////        }
////    )
////  .reduceByKey{
////    case (t1, t2) => {
////      t1
////    }
////  }
////    val o1 = queryResult
////  .map {
////    case (k, t) => {
////      (k.spatialKey, t)
////    }
////  }.collect()
////    val t = queryResult
////      .map {
////        case (k, t) => {
////          (k.spatialKey, t)
////        }
////      }
////      .aggregateByKey(MultibandTile(queryResult.first()._2.map{
////        case _ =>
////          0
////      }))({
////        (l, t)=>{
////          MultibandTile(
////            Array.concat(l.bands.toArray[Tile], Array(t))
////          )
////        }
////      }, {
////        (t1, t2) => {
//////          t1
////          MultibandTile(Array.concat(t1.bands.toArray[Tile], t2.bands.toArray[Tile]))//Array.concat(t1.bands.toArray[Tile], t2.bands.toArray[Tile])
////        }
////      })
////  .map{
////        case (k, mt) =>
////          (k, mt.combine(a=>{
////              val (c, _) = FPCA.run(sc, Vectors.dense(a.map(v => v.toDouble)))
////              c.toLocalMatrix().toArray.head.toInt
////            })
////          )
////}
////    val r = t.collect()
//    val irrdd = queryResult.map {
//      case (key, tile) =>
//        (key, Vectors.dense(tile.toArray().map(a => (a.toDouble))))
//    }.map {
//      case (key, vectors) =>
//        //        (((941932800000L-key.instant)/864000000).toInt, vectors)
//        IndexedRow(((941932800000L+(480L*864000000L) - key.instant) / 864000000).toInt, vectors)
//    }
//    val r = new IndexedRowMatrix(irrdd).toBlockMatrix().cache()
////  .collect()
//
//    val res = FPCA.run(sc,r)
//    val data = res._1.toLocalMatrix().toArray
//    val image: BufferedImage = new BufferedImage(10,10, BufferedImage.TYPE_INT_RGB)
//    for (y <- 0 until image.getHeight){
//      for (x <- 0 until image.getWidth){
//        val v = 255 * (data(y * image.getHeight + x) - data.min) / (data.max - data.min)
//        image.setRGB(x, y, new Color(v.toInt,v.toInt,v.toInt,v.toInt).getRGB)
//      }
//    }
//    val out = new File("data/out/pca.png")
//    ImageIO.write(image, "png", out)
//    println("------RDD read------")
//
//
////    log("----------Creating RDDs----------")
////    val sRdd = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
////      path = new Path(filePath),
////      uriToKey = {
////        case (uri, pExtent) => {
////          val _spl = FilenameUtils.getName(uri.toString).replace(".tif", "").split("-")
////          TemporalProjectedExtent(pExtent, ZonedDateTime.parse(f"${_spl.last}-${_spl(1)}-${_spl.head}T00:00:00Z", DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(5, 30))))
////        }
////      },
////      options = HadoopGeoTiffRDD.Options.DEFAULT
////    )
////    val (zoom, meta) = CollectTileLayerMetadata.fromRDD[TemporalProjectedExtent, MultibandTile, SpaceTimeKey](sRdd, FloatingLayoutScheme(256))
////
////    val minK: SpaceTimeKey = meta.bounds.get.minKey
////    val maxK: SpaceTimeKey = meta.bounds.get.maxKey
////    val updatedMeta = meta.updateBounds(KeyBounds(new SpaceTimeKey(minK.col, minK.row, 1262284200000L), new SpaceTimeKey(maxK.col, maxK.row, 1735669800000L)))
////    val tiled: RDD[(SpaceTimeKey, MultibandTile)] = sRdd.tileToLayout(
////      updatedMeta,
////      NearestNeighbor
////    )
////      .repartition(64)
////
////    val layoutScheme = ZoomedLayoutScheme(WebMercator, tileSize = 256)
////    val (_zoom, reprojected) = new TileRDDReprojectMethods(ContextRDD(tiled, updatedMeta)).reproject(layoutScheme, Bilinear)
////
////    log("-------RDD created-------")
////
////    val writer = FileLayerWriter(attributeStore)
////
////    def m(x: MultibandTile, y: MultibandTile): MultibandTile = {
////      y
////    }
////    Pyramid.upLevels(reprojected, layoutScheme, _zoom, NearestNeighbor){
////      (rdd, zoom) => {
////        log(f"Saving zoom $zoom")
////
////        if(attributeStore.layerExists(layerId = LayerId(layerName, zoom))){
//////          writer.update[
//////            SpaceTimeKey,
//////            MultibandTile,
//////            TileLayerMetadata[SpaceTimeKey]
//////          ](LayerId(layerName, zoom), rdd, mergeFunc = m)
////          writer.overwrite[
////            SpaceTimeKey,
////            MultibandTile,
////            TileLayerMetadata[SpaceTimeKey]
////          ](LayerId(layerName, zoom), rdd)
////        }else{
////          writer.write(LayerId(layerName, zoom), rdd, ZCurveKeyIndexMethod.byDay())
////        }
////        log(f"Saved zoom $zoom")
////      }
////    }
////    log(f"Saved $layerName")
//
//  }

  private def log(msg: String): Unit = {
    println(f"[APP_LOG] $msg")
  }
}
