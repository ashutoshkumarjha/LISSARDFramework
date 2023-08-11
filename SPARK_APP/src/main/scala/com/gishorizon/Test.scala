package com.gishorizon

import geotrellis.layer.{FloatingLayoutScheme, LayoutDefinition, SpaceTimeKey, SpatialKey, TileLayerMetadata}
import geotrellis.vector._
import geotrellis.raster._
import geotrellis.raster.geotiff.GeoTiffRasterSource
import geotrellis.raster.io.geotiff.reader.GeoTiffReader
import geotrellis.raster.mapalgebra.focal.Kernel
import geotrellis.raster.rasterize.Rasterizer

import scala.util.{Random, _}
import geotrellis.raster.render._
import geotrellis.spark.{MultibandTileLayerRDD, RasterSourceRDD}
import geotrellis.spark.tiling._
import geotrellis.store.LayerId
import geotrellis.store.file.FileCollectionLayerReader
import geotrellis.vector.io.json.JsonFeatureCollectionMap
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

import java.util.concurrent.atomic.LongAdder
import scala.collection.concurrent.TrieMap


/***
 * Sample Scala file for dev purposes only
 */
object Test{
//  def main(args: Array[String]): Unit = {
////    implicit val sc: SparkContext = Spark.context
////    val input = "data/output"
////
////    val aoiGj =
////      """
////        |{
////        |"type": "FeatureCollection",
////        |"name": "aoi",
////        |"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
////        |"features": [
////        |{ "id": "target_32a63e", "type": "Feature", "properties": { "id": "target_32a63e" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 77.886951735465502, 30.089349367852808 ], [ 77.971749834956611, 30.076255543666679 ], [ 77.951797340958706, 29.959658156866396 ], [ 77.852034870969163, 30.019515638860124 ], [ 77.886951735465502, 30.089349367852808 ] ] ] } }
////        |]
////        |}
////        |
////        |""".stripMargin
////    val aoi = aoiGj.extractGeometries[Polygon]().head
////    val init = () => new LongAdder
////    val update = (_: LongAdder).increment()
////    val data = FileCollectionLayerReader(input).read[SpaceTimeKey, Tile, TileLayerMetadata[SpaceTimeKey]](LayerId("Combined_Temporal_RDD", 0))
////    val pixelCounts: TrieMap[Int, LongAdder] = TrieMap.empty
////
////    data.foreach({
////      case (k, t) => {
////        val ex = data.metadata.mapTransform(k)
////        val re = RasterExtent(ex, data.metadata.layout.tileCols, data.metadata.layout.tileRows)
////
////        Rasterizer.foreachCellByPolygon(aoi, re){
////          case (col, row) => {
////            val pv = t.get(col, row).toInt
////            val acc = pixelCounts.getOrElseUpdate(pv, init())
////            update(acc)
////          }
////        }
////      }
////    })
////    val output = pixelCounts
////      .map { case (k, v) => k.toString -> v.sum.toInt }
////      .toMap
////
////    println(output)
////    //data.head._2.statistics.get.mean
//
//
//
////    val rasterSource = GeoTiffReader.readMultiband(input)
//////    val floatingLayoutScheme: FloatingLayoutScheme = FloatingLayoutScheme(10)
//////    val layout: LayoutDefinition = floatingLayoutScheme.levelFor(rasterSource.extent, rasterSource.cellSize).layout
////
////    val tl = TileLayout(1, rasterSource.tile.rows, rasterSource.tile.cols, 1)
////
////    val rowRdd: MultibandTileLayerRDD[SpatialKey] = RasterSourceRDD.spatial(
////      GeoTiffRasterSource(input),
////      LayoutDefinition(rasterSource.extent, tl)
////    )
////
////    println(rowRdd)
//
////    val extent = Extent(-109, 37, -102, 41)
////    val tl = TileLayout(4, 4, 10, 10)
////    val ld = LayoutDefinition
////    val layout: LayoutDefinition = LayoutDefinition(rasterSource.extent, tl)
////    def randomPointFeature(extent: Extent): PointFeature[Double] = {
////      def randInRange(low: Double, high: Double): Double = {
////        val x = Random.nextDouble
////        low * (1 - x) + high * x
////      }
////
////      Feature(Point(randInRange(extent.xmin, extent.xmax),
////        randInRange(extent.ymin, extent.ymax)),
////        Random.nextInt % 16 + 16)
////    }
////
////    val pts = (for (i <- 1 to 1000) yield randomPointFeature(extent)).toList
////
////    val kernelWidth: Int = 9
////    val kern: Kernel = Kernel.gaussian(kernelWidth, 1.5, 25)
////    val kde: Tile = pts.kernelDensity(kern, RasterExtent(extent, 700, 400))
//
////    val floatingLayoutScheme: FloatingLayoutScheme = FloatingLayoutScheme(1)
////    val numberOfBands: Int = rasterSource.bandCount
////    val layout: LayoutDefinition =
////      floatingLayoutScheme.levelFor(rasterSource.extent, rasterSource.cellSize).layout
////    val rdd: MultibandTileLayerRDD[SpatialKey] = RasterSourceRDD.spatial(GeoTiffRasterSource(inputs(0)), layout)
////
////    type MultibandRowRDD[K] = RDD[(K, List[List[Int]])] //with Metadata[TileLayerMetadata[K]]
////
////    val rowRdd: MultibandRowRDD[Int] = tileRDD.mapPartitions({
////      p =>
////        p.map {
////          case (k, t) => {
////            (k.row, (k, t))
////          }
////        }
////    }, preservesPartitioning = false)
////      .aggregateByKey[List[List[Int]]](List.empty)({
////        (l: List[List[Int]], t: (SpatialKey, MultibandTile)) => {
////          var temp = List[List[Int]]()
////          t._2.foreach {
////            v =>
////              temp = temp :+ v.toList
////          }
////          temp
////        }
////      }, {
////        (l1: List[List[Int]], l2: List[List[Int]]) => {
////          var temp = List[List[Int]]()
////          temp = temp :+ l1.head
////          temp = temp :+ l2.head
////          temp
////        }
////      })
////
////    println(rowRdd)
////
////    rasterSource.tile.bands.toList.head
//
//
//    //    type MultibandCellRDD[K] = RDD[(SpatialKey, List[Int])]
//    //    val cellRdd: MultibandCellRDD[Int] = tileRDD.mapPartitions({
//    //      p =>
//    //        p.map {
//    //          case (k, t) => {
//    //            (k, (k, t))
//    //          }
//    //        }
//    //    }, preservesPartitioning = false)
//    //      .aggregateByKey[List[Int]](List.empty)({
//    //      (l: List[Int], t: (SpatialKey, MultibandTile)) => {
//    //        var temp = List[Int]()
//    //        t._2.foreach {
//    //          v =>
//    //            temp = v.toList
//    //        }
//    //        temp
//    //      }
//    //    }, {
//    //      (l1: List[Int], l2: List[Int]) => {
//    //        l1
//    //      }
//    //    })
//    //    println(cellRdd)
//    //    val rdd: MultibandTileLayerRDD[SpatialKey] = RasterSourceRDD.spatial(GeoTiffRasterSource(inputs(0)), layout)
//
//
//    //    val testRdd: MultibandCellRDD[(Int, Int)] = rasterSource.tile.
//
//
//    //    rasterSource.tile.foreachDouble {
//    //      (a)=>{
//    //        a.length
//    //      }
//    //    }
//
//    //time rdd
//    //    val timeRDD = sc.parallelize(inputs, inputs.length)
//    //      .map {
//    //        (inputFile) => {
//    //          val (layer, meta) = multiBandTemporalStr(sc, inputFile, "", 4)
//    //          layer
//    //            .tileToLayout[SpaceTimeKey](meta.cellType, meta.layout)
//    //            .repartition(1).collect()
//    //        }}
//    //    println(timeRDD)
//
//
//    //    sc.parallelize()
//
//
//  }
}
