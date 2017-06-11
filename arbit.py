import requests, sqlite3, json, ConfigParser, uuid, time, pyodbc

#Keys
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('keys.cfg')
krakenkey = config.get("API", "kraken")
polokey = config.get("API", "polo")
geminikey = config.get("API", "gemini")
connstring = "Driver={ODBC Driver 13 for SQL Server};Server=tcp:"+config.get("DB","server")+";DATABASE="+config.get("DB","database")+";UID="+config.get("DB","uname")+";PWD="+ config.get("DB","pwd")

conn = pyodbc.connect(connstring)


