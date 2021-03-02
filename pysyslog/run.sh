#!/usr/bin/env python

## Tiny Syslog Server in Python.
##
## This is a tiny syslog server that is able to receive UDP based syslog
## entries on a specified port and save them to a file.
## That's it... it does nothing else...
## There are a few configuration parameters.

HOST, PORT = "0.0.0.0", 514
ANOMALY_DETECTOR = "detection-service"

import json
import re
import socketserver
import requests

haproxy_log_format = re.compile(r"^.* ([^ ]+) ([^ ]+)/([^ ]+) ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+) ([0-9]+) [^ ]+ [^ ]+ [^ ]+ ([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+)/([0-9]+) \"([A-Z]+) ([^ ]+) ([^ ]+)\".*$")

class SyslogUDPHandler(socketserver.BaseRequestHandler):

	def handle(self):
		data = bytes.decode(self.request[0].strip())
		socket = self.request[1]
		search = haproxy_log_format.search(str(data))
		if search:
			data = search.groups()
			log_entry = {
				"frontend":									data[0],
				"backend":									data[1],
				"server":									data[2],
				"time_to_receive_request":					data[3],
				"time_in_queue":							data[4],
				"time_to_tcp_connect":						data[5],
				"time_to_get_response":						data[6],
				"total_time_active":						data[7],
				"http_status":								data[8],
				"bytes_count":								data[9],
				"concurrent_connections_haproxy":			data[10],
				"concurrent_connections_frontend":			data[11],
				"concurrent_connections_backend":			data[12],
				"concurrent_active_connections_on_server":	data[13],
				"connection_retry_attempts":				data[14],
				"queue1":									data[15],
				"queue2":									data[16],
				"http_verb":								data[17],
				"http_path":								data[18],
				"http_protocol":							data[19]
			}
			try:
				response = requests.post('https://" + ANOMALY_DETECTOR + "/evaluate', data = log_entry)
				print("Got status code : " + str(response.status_code))
			except:
				print("Could not send data to " + ANOMALY_DETECTOR)

if __name__ == "__main__":
	try:
		server = socketserver.UDPServer((HOST,PORT), SyslogUDPHandler)
		server.serve_forever(poll_interval=0.5)
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		print ("Crtl+C Pressed. Shutting down.")
