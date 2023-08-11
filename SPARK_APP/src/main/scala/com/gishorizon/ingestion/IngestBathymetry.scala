package com.gishorizon.ingestion

import com.gishorizon.Spark
import geotrellis.layer.{FloatingLayoutScheme, LocalLayoutScheme, Metadata, SpaceTimeKey, SpatialKey, TemporalProjectedExtent, TileLayerMetadata, ZoomedLayoutScheme}
import geotrellis.proj4.WebMercator
import geotrellis.raster.resample.{Bilinear, NearestNeighbor}
import geotrellis.raster.{MultibandTile, Tile}
import geotrellis.spark.pyramid.Pyramid
import geotrellis.spark.reproject.TileRDDReprojectMethods
import geotrellis.spark.store.cog.COGLayer
import geotrellis.spark.store.file.{FileLayerReader, FileLayerWriter}
import geotrellis.spark.store.file.cog.{FileCOGLayerReader, FileCOGLayerWriter}
import geotrellis.spark.{CollectTileLayerMetadata, ContextRDD, TileLayerRDD, withTilerMethods}
import geotrellis.spark.store.hadoop.HadoopGeoTiffRDD
import geotrellis.store.{Intersects, LayerId, LayerQuery, Reader, ValueReader}
import geotrellis.store.file.FileAttributeStore
import geotrellis.store.index.ZCurveKeyIndexMethod
import geotrellis.vector.{Extent, Polygon, ProjectedExtent}
import org.apache.hadoop.fs.Path
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.locationtech.jts.geom.{Coordinate, LinearRing, PrecisionModel}

import java.net.URI
import java.time.{ZoneOffset, ZonedDateTime}
import java.time.format.DateTimeFormatter
import scala.collection.concurrent.TrieMap

object IngestBathymetry {
//  def main(args: Array[String]): Unit = {
//    val bathymetryPath = "data/in/liss3/04-01-2018.tif" //"/projects/biggis-framework/Data/input/LC08_L2SP_144039_20220609_20220616_02_T1_SR_B2.TIF" //
//    val outputCatalogPath = "data/out/liss3"
////    val outFilePath = "/home/mani/tmp/out/bathymetry"
//    val layerName = "liss3"
//
//    implicit val sc: SparkContext = Spark.context
//
//    val attributeStore = FileAttributeStore(outputCatalogPath)
//
//    log("----------Creating RDDs----------")
//    val sRdd = HadoopGeoTiffRDD[ProjectedExtent, ProjectedExtent, Tile](
//      path = new Path(bathymetryPath),
//      uriToKey = {
//        case (_, pExtent) => {
//          pExtent
//        }
//      },
//      options = HadoopGeoTiffRDD.Options.DEFAULT
//    )
//    val (zoom, meta) = CollectTileLayerMetadata.fromRDD[ProjectedExtent, Tile, SpatialKey](sRdd, FloatingLayoutScheme(256))
//    val tiled: RDD[(SpatialKey, Tile)] = sRdd.tileToLayout(meta, NearestNeighbor).repartition(64)
//
//    val layoutScheme = ZoomedLayoutScheme(WebMercator, tileSize = 256)
//    val (_zoom, reprojected) = new TileRDDReprojectMethods(ContextRDD(tiled, meta)).reproject(layoutScheme, Bilinear)
//
////    val contextRDD = ContextRDD(tiled, meta)
//
//    log("-------RDD created-------")
////    val (maxZoom, reprojected) = new TileRDDReprojectMethods(contextRDD).reproject(layoutSchemeOut, Bilinear)
//
//    val writer = FileLayerWriter(attributeStore)
//
//
//    Pyramid.upLevels(reprojected, layoutScheme, _zoom, NearestNeighbor){
//      (rdd, zoom) => {
//        log(f"Saving zoom $zoom")
//        writer.write(LayerId(layerName, zoom), rdd, ZCurveKeyIndexMethod)
//        log(f"Saved zoom $zoom")
//      }
//    }
//    log(f"Saved $layerName")
//
////    val writer = new FileCOGLayerWriter(attributeStore, new URI(outFilePath).getPath)
////    val cogLayer = COGLayer.fromLayerRDD(reprojected, maxZoom)
////    val keyIndex = cogLayer.metadata.zoomRangeInfos.map {
////      case (zr, bounds) => zr -> ZCurveKeyIndexMethod.createIndex(bounds)
////    }.toMap
////    writer.writeCOGLayer(layerName, cogLayer, keyIndex)
//
////    println("----------Bathymetry Ingested----------")
//
////    val reader = FileLayerReader(outputCatalogPath)
//////    val valueReader = ValueReader(new java.net.URI(outputCatalogPath))
////    val zoomLevels = attributeStore.layerIds.map{_.zoom}
////    val maxZoom = zoomLevels.max
////
//////    val layers = TrieMap.empty[Int, Reader[SpatialKey, Tile]]
////    val key = SpatialKey(1, 1)
////    val rdd = reader.read[SpatialKey, Tile, TileLayerMetadata[SpatialKey]](LayerId(layerName, 2)).filter{
////      case (k)=>{
////        k._1.col == key.col && k._1.row == key.row
////      }
////    }.collect()
//////    val t = reader.query[SpatialKey, Tile, TileLayerMetadata[SpatialKey]](LayerId(layerName, 6)).where(
//////      Intersects(new Extent(1,1, 2,2))
//////    ).result
//////    val reader = layers.getOrElseUpdate(1, valueReader.reader[SpatialKey, Tile](LayerId(layerName, 1)))
//////    val t = MultibandTile(reader(key))
////
////    println(rdd)
//
////    val result = reader.query[SpatialKey, Tile, TileLayerMetadata[SpatialKey]](LayerId(layerName, 6))
////      .where(
////        Intersects(new Extent(1,1, 2,2))
////      )
////      .result
////      .cache()
////    val result: TileLayerRDD[SpatialKey] = reader.read[SpatialKey, Tile, TileLayerMetadata[SpatialKey]](LayerId(layerName, 6))
////    val _data = result.collect().head
////    val png = _data._2.renderPng()
////    png.write(f"/home/mani/tmp/render/${_data._1.col}_${_data._1.row}.png")
////    _data.foreach {
////      case (k, t) => {
////        val png = t.renderPng()
////        png.write(f"/home/mani/tmp/render/${k.col}_${k.row}.png")
////      }
////    }
////    val rdd: TileLayerRDD[SpatialKey] = reader.read[SpatialKey, Tile](LayerId(layerName, 0))
////
////    val result = reader.query[SpatialKey, TileLayerMetadata[SpatialKey], RDD[(SpatialKey, Tile) with Metadata[TileLayerMetadata[SpatialKey]]]](LayerId(layerName, 0))
////      .where(
////      Intersects(
////        new Extent(8575592,3581729, 8793088,3781260)
////      )
////    ).result.cache()
////    val query: LayerQuery[SpatialKey, TileLayerMetadata[SpatialKey]] =
////      new LayerQuery[SpatialKey, TileLayerMetadata[SpatialKey]]
////        .where(Intersects(new Extent(8575592,3581729, 8793088,3781260)))
//
//  }

  private def log(msg: String): Unit = {
    println(f"[APP_LOG] $msg")
  }
}
