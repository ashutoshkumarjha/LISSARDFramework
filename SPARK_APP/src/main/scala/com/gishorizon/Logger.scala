package com.gishorizon

import org.joda.time.DateTime

object Logger {
def log(str: String): Unit = {
  println("[APP_LOG] " + DateTime.now() + str)
}
}
