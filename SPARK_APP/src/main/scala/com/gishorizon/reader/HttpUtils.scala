package com.gishorizon.reader

import play.api.libs.json.{JsObject, JsValue, Json}

import java.net.{HttpURLConnection, URL}
import scala.io.Source

object HttpUtils {

  def getRequest(urlStr: String, callback: (Boolean, JsValue) => Unit): Unit = {
    val url = new URL(urlStr)
    val connection = url.openConnection.asInstanceOf[HttpURLConnection]
    connection.setRequestMethod("GET")
    val responseCode = connection.getResponseCode
    if (responseCode == HttpURLConnection.HTTP_OK) {
      val inputStream = connection.getInputStream
      val responseBody = Source.fromInputStream(inputStream).mkString
      inputStream.close()
      val json: JsValue = Json.parse(responseBody)
      callback(true, json)
    } else {
      callback(false, null)
    }
    connection.disconnect()
  }

  def getRequestSync(urlStr: String): JsValue = {
    var json: JsValue = null
    val url = new URL(urlStr)
    val connection = url.openConnection.asInstanceOf[HttpURLConnection]
    connection.setRequestMethod("GET")
    val responseCode = connection.getResponseCode
    if (responseCode == HttpURLConnection.HTTP_OK) {
      val inputStream = connection.getInputStream
      val responseBody = Source.fromInputStream(inputStream).mkString
      inputStream.close()
      json = Json.parse(responseBody)
    }
    connection.disconnect()
    json
  }



}
