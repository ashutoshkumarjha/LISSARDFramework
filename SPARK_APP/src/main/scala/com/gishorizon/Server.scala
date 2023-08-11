package com.gishorizon

import akka.actor.ActorSystem

import scala.concurrent._
import scala.concurrent.Future
import ExecutionContext.Implicits.global
import akka.http.scaladsl.unmarshalling.Unmarshaller._
import akka.http.scaladsl.server.{HttpApp, Route}
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport._
import akka.http.scaladsl.model.{ContentType, HttpEntity, HttpResponse, MediaTypes}
import spray.json._
import com.typesafe.config.ConfigFactory
import ch.megard.akka.http.cors.scaladsl.CorsDirectives._
import com.gishorizon.ingestion.IngestData
import com.gishorizon.reader.ReadPyIngestion
import geotrellis.layer.{SpaceTimeKey, SpatialKey, TileLayerMetadata}
import org.apache.log4j.Logger
import geotrellis.proj4.{CRS, ConusAlbers, LatLng}
import geotrellis.raster._
import geotrellis.raster.rasterize.Rasterizer
import geotrellis.raster.render.GreaterThanOrEqualTo
import geotrellis.spark._
import geotrellis.spark.store.file.FileLayerReader
import geotrellis.store.LayerId
import geotrellis.store.file.FileCollectionLayerReader
import geotrellis.vector._
import geotrellis.vector.io._
import org.apache.spark.SparkContext
import spray.json._
import spray.json.DefaultJsonProtocol._

import java.util.concurrent.atomic.LongAdder
import scala.collection.concurrent.TrieMap
import com.gishorizon.operations._
import play.api.libs.json.{JsArray, JsObject, JsValue, Json}

case class IngestionRequest(sensor: String, srcPath: String, dataTime: String)
case class IngestionResponse(response: Map[String, String])
case class TestResponse(response: Map[String, String])
case class ProcessRequest(data: String)

object RequestResponseProtocol extends DefaultJsonProtocol {
  implicit val ingestRequest = jsonFormat3(IngestionRequest)
  implicit val processRequest = jsonFormat1(ProcessRequest)
  implicit val ingestResponse = jsonFormat1(IngestionResponse)
  implicit val testResponse = jsonFormat1(TestResponse)
}

object Server extends HttpApp with App {
  implicit val sc: SparkContext = Spark.context
  private val appConf = ConfigFactory.load()
  implicit val system: ActorSystem = ActorSystem("Server", appConf)

  import RequestResponseProtocol._
  val logger = Logger.getLogger(this.getClass.getName)

  def routes: Route = cors() {
    get {

      path("test" / Segment) {
        (sensor) => {
          complete {
            Future {
              ReadPyIngestion.run(sc)
              TestResponse(Map {
                "message" -> "Success"
              })
            }
          }
        }
      }

//      path("tile" / Segment / Segment / Segment / Segment) {
//        (layerName, _z, _x, _y) => {
//          parameters(
//            Symbol("startDt").as[String],
//            Symbol("endDt").as[String],
//            Symbol("bands").as[String],
//            Symbol("mode").as[String]
//          ) {
//            (startDt, endDt, bands, mode) => {
//              complete {
//                Future {
//                  val x = _x.toInt
//                  val y = _y.toInt
//                  val z = _z.toInt
//                  val startDtStr = startDt //dateQuery.split(':')(0)
//                  val endDtStr = endDt
//
//                  val (reader, maxZoom) = TileServerUtils.getCatalogDetails(
//                    sc, f"${appConf.getString("FILE_CATALOG_PATH")}${layerName}", layerName //layer("path")
//                  )
//                  var tls = TileServerUtils.getMultibandTileForXYZTime(
//                    reader, layerName, maxZoom, x, y, z, startDtStr, endDtStr
//                  )
//
//                  if(mode=="viz"){
//                    val _vizBands = bands.split(',').map(e => e.toInt)
//                    tls = tls.subsetBands(_vizBands)
//                      .map {
//                        (_, v) =>
//                          256 * v / 65536
//                      }
//                    if(tls.bandCount<3){
//                      val renderDivision = (0 until 255 by 1).toArray
//                      val png = tls.band(0).withNoData(Option(0.0)).renderPng(
//                        ColorMap(renderDivision, ColorRamps.greyscale(renderDivision.length))
//                      )
////                      val png = tls.band(0).withNoData(Option(0.0)).renderPng()
//                      HttpResponse(entity = HttpEntity(ContentType(MediaTypes.`image/png`), png.bytes))
//                    }else{
//                      val png = tls.withNoData(Option(0.0)).renderPng()
//                      HttpResponse(entity = HttpEntity(ContentType(MediaTypes.`image/png`), png.bytes))
//                    }
//                  }else{
//                    var min = -100
//                    var max = 100
//
////                    var mTileData = Array[Array[Double]]()
//                    var index = 0
//                    val _mTileData = Array.fill(256*256)(
//                      Array.fill(tls.bandCount)(0.0)
//                    )
//
//                    val niBands = bands.split(',').map(e => e.toInt)
//                    tls.subsetBands(niBands  ).toArrayTile().foreachDouble((v)=>{
//                      val xi = (index % 256)
//                      val yi = Math.floor(index.toDouble / 256).toInt
//                      _mTileData(((xi * 256) + yi)) = v
//                      index = index + 1
//                    })
////                    for(i <- mTileData.indices){
////                      val xi = (i%256).toInt
////                      val yi = Math.floor(i.toDouble/256).toInt
////                      _mTileData(((xi*256) + yi)) = mTileData(i)
////                    }
//                    val t: Tile = ArrayTile(
//                      sc.parallelize(_mTileData).map {
//                        case (v) => {
//                          if (v(0) == 0 && v(1) == 0) {
//                            (-99.0).toInt
//                          } else {
//                            ((v(1) - v(0)) / (v(1) + v(0)) * 100).toInt
//                          }
//                        }
//                      }.collect(),
//                      256,
//                      256
//                    ).withNoData(Option(-99))
//
//
////                    val t = tls.subsetBands(3, 4  ).combine(0, 1){
////                      case (a, b)=>{
////                        if(a==0 && b==0){
////                          -99
////                        }else{
////                          val v = ((
////                            (b.toDouble - a.toDouble) / (b.toDouble + a.toDouble)
////                            ) * 100).toInt
////                          v
////                        }
////                      }
////                    }.withNoData(Option(-99))
//
//                    val renderDivision = (min until max by 1).toArray
//                    val png = t.renderPng(
//                      ColorMap(renderDivision, ColorRamps.greyscale(renderDivision.length))
//                    )
//
//                    HttpResponse(entity = HttpEntity(ContentType(MediaTypes.`image/png`), png.bytes))
//                  }
//
//                }
//              }
//            }
//          }
//        }
//      }
    } ~ post {
        path("ingest") {
          entity(as[IngestionRequest]) { ingestionRequest =>
              complete {
              Future {
                IngestData.run(sc, ingestionRequest)
              }
            }
          }
        }
      path("process") {
        entity(as[ProcessRequest]) { processRequest =>
          complete {
            Future {
              val json: JsValue = Json.parse(processRequest.data)
              val inJsArray = json.asInstanceOf[JsObject].value("inputs").asInstanceOf[JsArray]
              val opJsArray = json.asInstanceOf[JsObject].value("operations").asInstanceOf[JsArray]

              val processConfig = new ProcessConfig()
              var inputs: Array[ProcessInput] = Array()
              var operations: Array[ProcessOperation] = Array()
              val output = new ProcessOutput()
              output.id = json.asInstanceOf[JsObject].value("output").asInstanceOf[JsObject].value("id").asInstanceOf[play.api.libs.json.JsString].value

              for(inJs <- inJsArray.value.indices){
                val iId = inJsArray.value(inJs).asInstanceOf[JsObject].value("id").asInstanceOf[play.api.libs.json.JsString].value
                val tIndexes = inJsArray.value(inJs).asInstanceOf[JsObject].value("tIndexes").asInstanceOf[JsArray].value.map(e=>e.as[BigInt]).toArray
                val aoiCode = inJsArray.value(inJs).asInstanceOf[JsObject].value("aoiCode").asInstanceOf[play.api.libs.json.JsString].value
                val dsName = inJsArray.value(inJs).asInstanceOf[JsObject].value("dsName").asInstanceOf[play.api.libs.json.JsString].value
                val pIn = new ProcessInput()
                pIn.id = iId
                pIn.tIndexes = tIndexes
                pIn.isTemporal = true
                pIn.aoiCode = aoiCode
                pIn.dsName = dsName
                inputs = inputs :+ pIn
              }
              for (opJs <- opJsArray.value.indices) {
                val iId = opJsArray.value(opJs).asInstanceOf[JsObject].value("id").asInstanceOf[play.api.libs.json.JsString].value
                val opInputs = opJsArray.value(opJs).asInstanceOf[JsObject].value("inputs").asInstanceOf[JsArray].value.map(e => {
                  val lId = e.asInstanceOf[JsObject].value("id").asInstanceOf[play.api.libs.json.JsString].value
                  val lBand = e.asInstanceOf[JsObject].value("band").asInstanceOf[play.api.libs.json.JsNumber].value
                  val opIn = new ProcessInput()
                  opIn.id = lId
                  opIn.band = lBand.toInt
                  opIn
                }).toArray
                val opType = opJsArray.value(opJs).asInstanceOf[JsObject].value("type").asInstanceOf[play.api.libs.json.JsString].value
                val opParams = opJsArray.value(opJs).asInstanceOf[JsObject].value("params").asInstanceOf[play.api.libs.json.JsString].value
                val opOutput = new ProcessOutput()
                val opId = opJsArray.value(opJs).asInstanceOf[JsObject].value("output").asInstanceOf[JsObject].value("id").asInstanceOf[play.api.libs.json.JsString].value
                opOutput.id = opId
                val pIn = new ProcessOperation()
                pIn.id = iId
                pIn.opType = opType
                pIn.inputs = opInputs
                pIn.output = opOutput
                pIn.params = opParams
                operations = operations :+ pIn
              }

              processConfig.inputs = inputs
              processConfig.output = output
              processConfig.operations = operations

              val result = WorkProcess.run(processConfig)

              Map {
                "message" -> "Success"
                "data" -> result
              }
            }
          }
        }
      }
      }
  }

  startServer(appConf.getString("server-host"), appConf.getInt("server-port"))

}

/***
 * Sample request
 * curl --request POST   --url http://localhost:8087/histogramForAoi   --header 'content-type: application/json'   --data '{"geometry":"{\"type\":\"Polygon\",\"coordinates\":[ [ [ 77.886951735465502, 30.089349367852808 ], [ 77.971749834956611, 30.076255543666679 ], [ 77.951797340958706, 29.959658156866396 ], [ 77.852034870969163, 30.019515638860124 ], [ 77.886951735465502, 30.089349367852808 ] ] ]}"}'
 * //              val layer = DataConfigs.Layers(layerName)
 * //              val stepValue = (DataConfigs.RenderStyles(layer("render"))("max") - DataConfigs.RenderStyles(layer("render"))("min")) / DataConfigs.RenderStyles(layer("render"))("numSteps")
 * //              val renderDivision = (DataConfigs.RenderStyles(layer("render"))("min") until DataConfigs.RenderStyles(layer("render"))("max") by stepValue).toArray
 * //              ColorMap(renderDivision, ColorRamps.ClassificationMutedTerrain.stops(renderDivision.length))
 *
 */