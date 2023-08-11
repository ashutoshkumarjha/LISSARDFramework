//References :https://github.com/geotrellis/geotrellis-spark-job.g8
//References :https://geotrellis.github.io/geotrellis-workshop/docs/spark-layer-rdd
//Torun on sbt-shell put
//test:runMain com.gishorizon.Main --inputs /Users/ManiChan/Geotrellis/TimeAnalysis/data/LE07_L2SP_143042_20050203_20200915_02_T1_SR_B2.TIF --output file:///Users/ManiChan/Geotrellis/TimeAnalysis/data/LE07_L2SP_143042_20050203_20200915_02_T1_SR_B2.TIF.cat --numPartitions 3
//test:runMain com.gishorizon.Main --inputs data/NDVISampleTest/Test1998-99.tif --output file:///Users/ashutosh/Geotrellis/TimeAnalysis/data/LE07_L2SP_143042_20050203_20200915_02_T1_SR_B2.TIF.cat --numPartitions 3

package com.gishorizon

import cats.implicits._
import com.gishorizon.operations.{FpcaDev, FpcaTemporal, NDI, ProcessInput, ProcessOperation}
import com.monovore.decline._
import geotrellis.layer._
import geotrellis.raster._
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.spark.store.RasterReader
import geotrellis.spark.store.hadoop.HadoopGeoTiffRDD
import geotrellis.spark.{merge, _}
import geotrellis.vector._
import org.apache.hadoop.fs.Path
import org.apache.spark._
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.linalg.distributed.IndexedRow
import org.apache.spark.rdd._
import org.joda.time.DateTime
import org.log4s._

import java.time.format.DateTimeFormatter
import java.time.{Instant, ZoneOffset, ZonedDateTime}
import scala.util.Random

//import geotrellis.raster.io.geotiff.GeoTiffReader

object  Main {
  @transient private[this] lazy val logger = getLogger

  private val inputsOpt = Opts.options[String](
    "inputs", help = "The path that points to data that will be read")
  private val outputOpt = Opts.option[String](
    "output", help = "The path of the output tiffs")
  private val partitionsOpt =  Opts.option[Int](
    "numPartitions", help = "The number of partitions to use").orNone

  private val command = Command(name = "geotrellis-spark-job", header = "GeoTrellis App: geotrellis-spark-job") {
    (inputsOpt, outputOpt, partitionsOpt).tupled
  }
  def main(args: Array[String]): Unit = {
    val sc: SparkContext = Spark.context
//    val p = "hdfs://localhost:9000/LC08_L2SP_144039_20191226_20200824_02_T1_SR.tif"
//    val layer: RDD[(ProjectedExtent, MultibandTile)] = HadoopGeoTiffRDD[ProjectedExtent, ProjectedExtent, MultibandTile](
//      path = new Path(p),
//      uriToKey = {
//        case (uri, projectedExtent) =>
//          projectedExtent
//      },
//      options = HadoopGeoTiffRDD.Options.DEFAULT
//    )(sc, RasterReader.multibandGeoTiffReader)
//    val (zoom, meta) = CollectTileLayerMetadata.fromRDD[ProjectedExtent, MultibandTile, SpatialKey](layer, FloatingLayoutScheme(256))
//    var tiled: RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]] = ContextRDD(
//      layer.tileToLayout(meta.cellType, meta.layout),
//      meta
//    )
//    tiled.collect()
//    print(tiled)

//    val d1: Array[Double] = Array(3, 2, 5, 1, 4, 5, 2, 3, 5, 4, 3, 2)
//    val d2: Array[Double] = Array(3, 2, 5, 1, 4, 5, 2, 3, 5, 4, 3, 2)
//    val d3: Array[Double] = Array(5, 2, 3, 1, 4, 5, 2, 3, 5, 4, 3, 2)
//    val d4: Array[Double] = Array(3, 2, 2, 1, 4, 5, 2, 3, 5, 4, 3, 2)
//    val d5: Array[Double] = Array(3, 2, 4, 1, 4, 5, 2, 3, 5, 4, 3, 2)
//    val bpPts1 = IndexedRow(0, Vectors.dense(d1))
//    val bpPts2 = IndexedRow(1, Vectors.dense(d2))
//    val bpPts3 = IndexedRow(2, Vectors.dense(d3))
//    val bpPts4 = IndexedRow(3, Vectors.dense(d4))
//    val bpPts5 = IndexedRow(4, Vectors.dense(d5))
//    println(DateTime.now().toString() + "----------------START-----------------")
//    for(i <- 0 to 655360){
//      val out = FpcaDev.normalCompute(Array(bpPts1, bpPts2, bpPts3, bpPts4, bpPts5))
//    }
//    println(DateTime.now().toString() + "----------------END-----------------")

//    var dir = "G:/ProjectData/tiles/Landsat_OLI/12/3060/1734/"
    val f1 = "G:/ProjectData/tiles/Landsat_OLI/12/3060/1734/1690659094429.tif"
    val f2 = "G:/ProjectData/tiles/Landsat_OLI/12/3060/1734/1690659094449.tif"
    val f3 = "G:/ProjectData/tiles/Landsat_OLI/12/3060/1735/1690659094489.tif"
    val ps = Array(f1, f2, f3)
    var rdd: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = RddUtils.getMultiTiledTemporalRDDWithMeta(
      sc, ps, 256
    )

    val o = rdd
    val tPath = DataConfigs.TEMP_PATH
    val outMeta = o.metadata
    val fPaths = o
      .map { case (key, tile) => (key.instant, (key.spatialKey, tile)) }
      .groupByKey()
      .map {
        case (t, d) => {
          val od: RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]] = ContextRDD(Spark.context.parallelize(d.toSeq), TileLayerMetadata(outMeta.cellType, outMeta.layout, outMeta.extent, outMeta.crs, outMeta.bounds.asInstanceOf[Bounds[SpatialKey]]))
          val raster: Raster[MultibandTile] = od.stitch
          println("Stitch complete")
          val fPath = f"$tPath${
            Iterator.continually(Random.nextPrintableChar)
              .filter(_.isLetter)
              .take(16)
              .mkString
          }.tif"
          GeoTiff(raster, o.metadata.crs).write(fPath)
          fPath
        }
      }.collect()

//    var bm = "fpca"
//    if(args.length > 0){
//      dir = args(0)
//    }
//    if (args.length > 1) {
//      bm = args(1)
//    }
//    if (args.length > 2) {
//      //tile path
//      DataConfigs.SPARK_MASTER = args(2)
//    }
//    if (args.length > 3) {
//      //tile path
//      DataConfigs.DRI_MEM = args(3)
//    }
//    if (args.length > 4) {
//      //tile path
//      DataConfigs.EXE_MEM = args(4)
//    }
//    if(bm=="fpca"){
//      val ps = Array(
//        dir + "1690659094389.tif",
//        dir + "1690659094399.tif",
//        dir + "1690659094409.tif",
//        dir + "1690659094419.tif",
//        dir + "1690659094429.tif",
//        dir + "1690659094439.tif",
//        dir + "1690659094449.tif",
//        dir + "1690659094459.tif",
//        dir + "1690659094469.tif"
//      )
//      var rdd: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = null
//      for (p <- ps) {
//        val layer: RDD[(TemporalProjectedExtent, MultibandTile)] = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
//          path = new Path(p),
//          uriToKey = {
//            case (uri, projectedExtent) =>
//              val ts = uri.toString.split("/").last.replace(".tif", "").toLong
//              TemporalProjectedExtent(projectedExtent, ZonedDateTime.ofInstant(
//                Instant.ofEpochMilli((ts))
//                , DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)).getZone
//              ))
//          },
//          options = HadoopGeoTiffRDD.Options.DEFAULT
//        )(sc, RasterReader.multibandGeoTiffReader)
//        val (zoom, meta) = CollectTileLayerMetadata.fromRDD[TemporalProjectedExtent, MultibandTile, SpaceTimeKey](layer, FloatingLayoutScheme(256))
//        var tiled: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(
//          layer.tileToLayout(meta.cellType, meta.layout),
//          meta
//        )
//
//        val inputNdi = new ProcessInput()
//        inputNdi.id = "I1"
//        val operation = new ProcessOperation()
//        operation.id = "op_ndi"
//        operation.inputs = Array(inputNdi, inputNdi)
//        operation.params = "I1:3#I2:4"
//        val i: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Map(
//          "I1" -> tiled,
//          "I2" -> tiled
//        )
//        println("----------------START-----------------")
//        tiled = NDI.runProcess(i, operation)
//        println("----------------END-----------------")
//
//        if (rdd == null) {
//          rdd = tiled
//        } else {
//          rdd = tiled.merge(rdd)
//        }
//      }
//
//      val input1 = new ProcessInput()
//      input1.id = "I1"
//      val input2 = new ProcessInput()
//      input2.id = "I2"
//      val input3 = new ProcessInput()
//      input3.id = "I3"
//      val input4 = new ProcessInput()
//      input4.id = "I4"
//      val input5 = new ProcessInput()
//      input5.id = "I5"
//
//      val operation = new ProcessOperation()
//      operation.id = "op_fpca"
//      operation.inputs = Array(input1, input2, input3, input4, input5)
//      val i: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Map(
//        "I1" -> rdd,
//        "I2" -> rdd,
//        "I3" -> rdd,
//        "I4" -> rdd,
//        "I5" -> rdd
//      )
//
//      val o = FpcaTemporal.runProcess(i, operation)
//      println("[APP_LOG] " + DateTime.now() + "FPCA Start...")
//
//      val tPath = DataConfigs.TEMP_PATH
//      val outMeta = o.metadata
//      val fPaths = o
//        .map { case (key, tile) => (key.instant, (key.spatialKey, tile)) }
//        .groupByKey()
//        .map {
//          case (t, d) => {
//            val od: RDD[(SpatialKey, MultibandTile)] with Metadata[TileLayerMetadata[SpatialKey]] = ContextRDD(Spark.context.parallelize(d.toSeq), TileLayerMetadata(outMeta.cellType, outMeta.layout, outMeta.extent, outMeta.crs, outMeta.bounds.asInstanceOf[Bounds[SpatialKey]]))
//            val raster: Raster[MultibandTile] = od.stitch
//            println("Stitch complete")
//            val fPath = f"$tPath${
//              Iterator.continually(Random.nextPrintableChar)
//                .filter(_.isLetter)
//                .take(16)
//                .mkString
//            }.tif"
//            GeoTiff(raster, o.metadata.crs).write(fPath)
//            fPath
//          }
//        }.collect()
//      println("[APP_LOG] " + DateTime.now() + "FPCA End...")
//    }else{
//      val p = dir + "1690659094509.tif"
//      val layer: RDD[(TemporalProjectedExtent, MultibandTile)] = HadoopGeoTiffRDD[ProjectedExtent, TemporalProjectedExtent, MultibandTile](
//        path = new Path(p),
//        uriToKey = {
//          case (uri, projectedExtent) =>
//            val ts = uri.toString.split("/").last.replace(".tif", "").toLong
//            TemporalProjectedExtent(projectedExtent, ZonedDateTime.ofInstant(
//              Instant.ofEpochMilli((ts))
//              , DateTimeFormatter.ISO_INSTANT.withZone(ZoneOffset.ofHoursMinutes(0, 0)).getZone
//            ))
//        },
//        options = HadoopGeoTiffRDD.Options.DEFAULT
//      )(sc, RasterReader.multibandGeoTiffReader)
//      val (zoom, meta) = CollectTileLayerMetadata.fromRDD[TemporalProjectedExtent, MultibandTile, SpaceTimeKey](layer, FloatingLayoutScheme(256))
//      val tiled: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(
//        layer.tileToLayout(meta.cellType, meta.layout),
//        meta
//      )
//
//      val input1 = new ProcessInput()
//      input1.id = "I1"
//      val input2 = new ProcessInput()
//      input2.id = "I2"
//
//      val operation = new ProcessOperation()
//      operation.id = "op_ndi"
//      operation.inputs = Array(input1, input2)
//      operation.params = "I1:3#I2:4"
//      val i: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Map(
//        "I1" -> tiled,
//        "I2" -> tiled
//      )
//      println("----------------START-----------------")
//      NDI.runProcess(i, operation).collect()
//      println("----------------END-----------------")
//    }
  }
}
