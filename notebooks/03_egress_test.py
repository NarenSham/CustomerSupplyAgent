# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# Which external hosts can Free Edition compute reach? Decides whether a voice worker could run on Databricks.
import urllib.request, urllib.error

for url in ["https://api.deepgram.com", "https://livekit.io", "https://api.elevenlabs.io", "https://pypi.org"]:
    try:
        urllib.request.urlopen(url, timeout=5)
        print("REACHABLE", url)
    except urllib.error.HTTPError as e:
        print("REACHABLE", url, e.code)        # an HTTP error still means the host answered
    except Exception as e:
        print("BLOCKED?", url, type(e).__name__)

# COMMAND ----------

