"""
<Purpose>
  The purpose of this server is to start up a webserver, mostly
  for the convenient of testing our softwareupdater. To be backward
  compatible with repyV1, we use librepy along with registerhttpcallback.
"""

import os
import sys

from repyportability import *
_context = locals()
add_dy_support(_context)

# Librepy is used to be backward compatible with repyV1
# since we are using the old httpserver.
dy_import_module_symbols("librepy.repy")
dy_import_module_symbols("httpserver.repy")

#webserver functionality based off the old webserver
def callbackfunc(request_dictionary):
  
  response_dict = {'version' : '1.0',
                   'statuscode' : 100,
                   'statusmsg' : 'OK',
                   'headers' : {'HTTP' : 'OK'},
                   'message' : None
                   }

  msg = request_dictionary['path']
  if msg == 400:
    response = '<h1>400 Bad Request</h1>'
    response_dict['statuscode'] = 400


  elif msg == 414:
    response = '<h1>414 URI Too Long</h1>'
    response_dict['statuscode'] = 414
    response_dict['statusmsg'] = 'URI Too Long'

  else:
    files = listfiles()

    # Create a message with the list of the files in the current directory
    if(msg == '/'): 
      response = '<h1>Files in Current Directory</h1>'
      for file in files:
        temp = '<p>' + file + '</p>'
        response += temp

    # Get the contents of a specific file
    else:  
      msg = msg.strip('/')
      found = 0
      for file in files:
        if(file == msg):
          found = 1
          response = ''
          try:
            fd = open(file, 'r')
            response += fd.read()
            fd.close()
            response_dict['statuscode'] = 200
            response_dict['statusmsg'] = 'OK'
          except:
            response = '<h1> File could not be opened or read</h1>'
            response_dict['statuscode'] = 403
            response_dict['statusmsg'] = 'File could not be opened or read.'
      if(found == 0):
        response_dict['statuscode'] = 404
        response = '<h1>File Not Found</h1>'
        response_dict['statusmsg'] = 'File Not Found'

  response_dict['message'] = response

  return response_dict




def main():
  address_tuple = (getmyip(), 12345)

  os.chdir(sys.argv[1])
  curdir = os.getcwd()

  print "Starting webserver on the directory: " + curdir
  httpserver_registercallback(address_tuple, callbackfunc)
  while True:
    sleep(10)
  
  
if __name__ == "__main__":
  main()

