package com.gishorizon.operations

import geotrellis.layer.{Metadata, SpaceTimeKey, SpatialKey, TemporalKey, TileLayerMetadata}
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.raster.{ArrayTile, MultibandTile, Tile, io => _, _}
import geotrellis.spark.{ContextRDD, MultibandTileLayerRDD, _}
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.linalg.distributed._
import org.apache.spark.rdd.RDD
import org.joda.time._

object FpcaTemporal {

    def runProcess(inputs: Map[String, RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]], processOperation: ProcessOperation)
    : RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]
    = {

      var meta: TileLayerMetadata[SpaceTimeKey] = null
      var irdds: Array[RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]]] = Array()
      for(i <- processOperation.inputs.indices){
        var inrdd:  RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = inputs(processOperation.inputs(i).id)
        inrdd = ContextRDD(inrdd.map {
          case (k, v) => {
            (k.spatialKey, (k.instant.toLong, v))
          }
        }
          .reduceByKey(
            (t1: (Long, MultibandTile), t2: (Long, MultibandTile)) => {
              var bds1: Array[Tile] = Array()
              for (i <- t1._2.bands) {
                bds1 = bds1 :+ i.convert(CellType.fromName("float32")).mapDouble(c=>c)
              }
              for (i <- t2._2.bands) {
                bds1 = bds1 :+ i.convert(CellType.fromName("float32")).mapDouble(c=>c)
              }

              val t: MultibandTile = ArrayMultibandTile(bds1)
              (t1._1, t)
            }
          ).map {
          case (k, v) => {
            (SpaceTimeKey(k, TemporalKey(v._1)), v._2)
          }
        }, inrdd.metadata)
        irdds = irdds :+ inrdd
        meta = inrdd.metadata
      }


      val outRdd: RDD[(SpaceTimeKey, MultibandTile)] = irdds.reduce {
        (rdd1, rdd2) => {
          val rdd: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(rdd1.++(rdd2), rdd1.metadata)
          rdd
        }
      }.map {
        case (k, v) => {
          (k.spatialKey, v)
        }
      }.aggregateByKey{
        Array[Array[IndexedRow]]()
      }({
        (l, r) => {
          var i = 0
          var irs: Array[Array[IndexedRow]] = Array()
          r.toArrayTile().foreachDouble((v => {
            irs = irs :+ Array(IndexedRow(i, Vectors.dense(v)))
            i = i + 1
          }))
          irs
        }
      }, (l1, l2)=>{
        var irs: Array[Array[IndexedRow]] = Array()
        for(i <- l1.indices){
          var ir: Array[IndexedRow] = Array()
          for(j <- l1(i).indices){
            ir = ir :+ l1(i)(j)
          }
          for (j <- l2(i).indices) {
            ir = ir :+ l1(i)(j)
          }
          irs = irs :+ ir
        }
        irs
      }).map {
        case (k, v) => {
          println("[APP_LOG] " + DateTime.now() + "Running FPCA")
          val o: Array[Array[Double]] = v.map {
            __v => {
              if (__v.forall(p =>
                p.vector.toArray.forall(_p => !_p.isNaN)
              )) {
                val (r, comps) = FpcaDev.normalCompute(__v)
                if (r == null) {
                  (0 until __v(0).vector.size).map(_ => 0.0).toArray[Double]
                } else {
                  val _a = r.toArray
                  _a
                }
              } else {
                (0 until __v(0).vector.size).map(_ => 0.0).toArray[Double]
              }
            }
          }
          var _o = Array[Array[Double]]()
          for (i <- o.indices) {
            val _t = Array[Double]()
            for (j <- o(i).indices) {
              if (_o.length <= j) {
                _o = _o :+ _t
              }
              _o(j) = _o(j) :+ o(i)(j)
            }
          }
          println("[APP_LOG] " + DateTime.now() + "FPCA tile generation...")
          (SpaceTimeKey(k, meta.bounds.get.maxKey.time), MultibandTile(
            _o.map {
              _v => {
                val at: Tile = ArrayTile(_v.map {
                  ___v => {
                    ___v
                  }
                }, 256, 256)
                at.rotate270.flipVertical
              }
            }
          ))
        }
      }
      val rdd: RDD[(SpaceTimeKey, MultibandTile)] with Metadata[TileLayerMetadata[SpaceTimeKey]] = ContextRDD(outRdd, meta)
      rdd
    }
  def write(tiles: MultibandTileLayerRDD[SpatialKey], path: String): Unit = {
    GeoTiff(tiles.stitch().tile, tiles.metadata.extent, tiles.metadata.crs).write(path)
  }

}
