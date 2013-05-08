#TODO(sjs25): Make the webserver use httpserver.repy and not registerhttpcallback
#This is meant to be a temporary fix so that the softwareupdater tests have 
#something to work with. They instead should be using Conrad and Yafete's
#httpserver.repy. However, at the time this was written, there existed
#a registerhttpcallback.repy file which this file included, and this 
#webserver is based on that code. In an effort to not fail at keeping up with
#current versions, this code will be used until httpserver.repy works with
#the encapsulatedwebserver.mix file.

#begin include registerhttpcallback.repy
"""
<Program Name>
  registerhttpcallback.repy

<Started>
  July 29, 2009

<Author>
  Yafete Yemuru

<Purpose>
  This program is Web server that a user can use without understanding http protocol.
  Given a URL this program acts like a web server that places a call back callbackfunc when a
  client(web browser) makes a connection to a given URL. The call back function is meant to
  modify a dynamic page using query and posted data. Once the call back return the modified
  version of the website the registerhttpcallback will complete the process by sending the
  web site content to the client(web browser).

"""


#begin include urllib.repy
def urllib_quote(string, safe="/"):
  """
  <Purpose>
    Encode a string such that it can be used safely in a URL or XML
    document.

  <Arguments>
    string:
           The string to urlencode.

    safe (optional):
           Specifies additional characters that should not be quoted --
           defaults to "/".

  <Exceptions>
    TypeError if the safe parameter isn't an enumerable.

  <Side Effects>
    None.

  <Returns>
    Urlencoded version of the passed string.
  """

  resultstr = ""

  # We go through each character in the string; if it's not in [0-9a-zA-Z]
  # we wrap it.

  safeset = set(safe)

  for char in string:
    asciicode = ord(char)
    if (asciicode >= ord("0") and asciicode <= ord("9")) or \
        (asciicode >= ord("A") and asciicode <= ord("Z")) or \
        (asciicode >= ord("a") and asciicode <= ord("z")) or \
        asciicode == ord("_") or asciicode == ord(".") or \
        asciicode == ord("-") or char in safeset:
      resultstr += char
    else:
      resultstr += "%%%02X" % asciicode

  return resultstr




def urllib_quote_plus(string, safe=""):
  """
  <Purpose>
    Encode a string to go in the query fragment of a URL.

  <Arguments>
    string:
           The string to urlencode.

    safe (optional):
           Specifies additional characters that should not be quoted --
           defaults to the empty string.

  <Exceptions>
    TypeError if the safe parameter isn't a string.

  <Side Effects>
    None.

  <Returns>
    Urlencoded version of the passed string.
  """

  return urllib_quote(string, safe + " ").replace(" ", "+")




def urllib_unquote(string):
  """
  <Purpose>
    Unquote a urlencoded string.

  <Arguments>
    string:
           The string to unquote.

  <Exceptions>
    ValueError thrown if the last wrapped octet isn't a valid wrapped octet
    (i.e. if the string ends in "%" or "%x" rather than "%xx". Also throws
    ValueError if the nibbles aren't valid hex digits.

  <Side Effects>
    None.

  <Returns>
    The decoded string.
  """

  resultstr = ""

  # We go through the string from end to beginning, looking for wrapped
  # octets. When one is found we add it (unwrapped) and the following
  # string to the resultant string, and shorten the original string.

  while True:
    lastpercentlocation = string.rfind("%")
    if lastpercentlocation < 0:
      break

    wrappedoctetstr = string[lastpercentlocation+1:lastpercentlocation+3]
    if len(wrappedoctetstr) != 2:
      raise ValueError("Quoted string is poorly formed")

    resultstr = \
        chr(int(wrappedoctetstr, 16)) + \
        string[lastpercentlocation+3:] + \
        resultstr
    string = string[:lastpercentlocation]

  resultstr = string + resultstr
  return resultstr




def urllib_unquote_plus(string):
  """
  <Purpose>
    Unquote the urlencoded query fragment of a URL.

  <Arguments>
    string:
           The string to unquote.

  <Exceptions>
    ValueError thrown if the last wrapped octet isn't a valid wrapped octet
    (i.e. if the string ends in "%" or "%x" rather than "%xx". Also throws
    ValueError if the nibbles aren't valid hex digits.

  <Side Effects>
    None.

  <Returns>
    The decoded string.
  """

  return urllib_unquote(string.replace("+", " "))




def urllib_quote_parameters(dictionary):
  """
  <Purpose>
    Encode a dictionary of (key, value) pairs into an HTTP query string or
    POST body (same form).

  <Arguments>
    dictionary:
           The dictionary to quote.

  <Exceptions>
    None.

  <Side Effects>
    None.

  <Returns>
    The quoted dictionary.
  """

  quoted_keyvals = []
  for key, val in dictionary.items():
    quoted_keyvals.append("%s=%s" % (urllib_quote(key), urllib_quote(val)))

  return "&".join(quoted_keyvals)




def urllib_unquote_parameters(string):
  """
  <Purpose>
    Decode a urlencoded query string or POST body.

  <Arguments>
    string:
           The string to decode.

  <Exceptions>
    ValueError if the string is poorly formed.

  <Side Effects>
    None.

  <Returns>
    A dictionary mapping keys to values.
  """

  keyvalpairs = string.split("&")
  res = {}

  for quotedkeyval in keyvalpairs:
    # Throw ValueError if there is more or less than one '='.
    quotedkey, quotedval = quotedkeyval.split("=")
    key = urllib_unquote_plus(quotedkey)
    val = urllib_unquote_plus(quotedval)
    res[key] = val

  return res

#end include urllib.repy
#begin include urlparse.repy  
"""
<Program Name>
  urlparse.repy

<Started>
  May 15, 2009

<Author>
  Michael Phan-Ba

<Purpose>
  Provides utilities for parsing URLs, based on the Python 2.6.1 module urlparse.

"""


def urlparse_urlsplit(urlstring, default_scheme="", allow_fragments=True):
  """
  <Purpose>
    Parse a URL into five components, returning a dictionary.  This corresponds
    to the general structure of a URL:
    scheme://netloc/path;parameters?query#fragment.  The parameters are not
    split from the URL and individual componenets are not separated.

    Only absolute server-based URIs are currently supported (all URLs will be
    parsed into the components listed, regardless of the scheme).

  <Arguments>
    default_scheme:
      Optional: defaults to the empty string.  If specified, gives the default
      addressing scheme, to be used only if the URL does not specify one.

    allow_fragments:
      Optional: defaults to True.  If False, fragment identifiers are not
      allowed, even if the URL's addressing scheme normally does support them.

  <Exceptions>
    ValueError on parsing a non-numeric port value.

  <Side Effects>
    None.

  <Returns>
    A dictionary containing:

    Key         Value                               Value if not present
    ============================================================================
    scheme      URL scheme specifier                empty string
    netloc      Network location part               empty string
    path        Hierarchical path                   empty string
    query       Query component                     empty string
    fragment    Fragment identifier                 empty string
    username    User name                           None
    password    Password                            None
    hostname    Host name (lower case)              None
    port        Port number as integer, if present  None

  """

  components = {"scheme": default_scheme, "netloc": "", "path": "", "query": "",
    "fragment": "", "username": None, "password": None, "hostname": None,
    "port": None }

  # Extract the scheme, if present.
  (lpart, rpart) = _urlparse_splitscheme(urlstring)
  if lpart:
    components["scheme"] = lpart

  # Extract the server information, if present.
  if rpart.startswith("//"):
    (lpart, rpart) = _urlparse_splitnetloc(rpart, 2)
    components["netloc"] = lpart

    (components["username"], components["password"], components["hostname"],
      components["port"]) = _urlparse_splitauthority(lpart)

  # Extract the fragment.
  if allow_fragments:
    (rpart, components["fragment"]) = _urlparse_splitfragment(rpart)


  # Extract the query.
  (components["path"], components["query"]) = _urlparse_splitquery(rpart)

  return components


def _urlparse_splitscheme(url):
  """Parse the scheme portion of the URL"""
  # The scheme is valid only if it contains these characters.
  scheme_chars = \
    "abcdefghijklmnopqrstuvwxyz0123456789+-."

  scheme = ""
  rest = url

  spart = url.split(":", 1)
  if len(spart) == 2:

    # Normalize the scheme.
    spart[0] = spart[0].lower()

    # A scheme is valid only if it starts with an alpha character.
    if spart[0] and spart[0][0].isalpha():
      for char in spart[0]:
        if char not in scheme_chars:
          break
      (scheme, rest) = spart

  return scheme, rest


def _urlparse_splitnetloc(url, start=0):
  """Parse the netloc portion of the URL"""

  # By default, the netloc is delimited by the end of the URL.
  delim = len(url)

  # Find the left-most delimiter.
  for char in "/?#":
    xdelim = url.find(char, start)
    if xdelim >= 0:
      delim = min(delim, xdelim)

  # Return the netloc and the rest of the URL.
  return url[start:delim], url[delim:]


def _urlparse_splitauthority(netloc):
  """Parse the authority portion of the netloc"""

  # The authority can have a userinfo portion delimited by "@".
  authority = netloc.split("@", 1)

  # Default values.
  username = None
  password = None
  hostname = None
  port = None

  # Is there a userinfo portion?
  if len(authority) == 2:

    # userinfo can be split into username:password
    userinfo = authority[0].split(":", 1)

    # hostport can be split into hostname:port
    hostport = authority[1].split(":", 1)

    if userinfo[0]:
      username = userinfo[0]
    if len(userinfo) == 2:
      password = userinfo[1]

  # No userinfo portion found.
  else:

    # hostport can be split into hostname:port
    hostport = netloc.split(":", 1)

  # Is there a port value?
  if hostport[0]:
    hostname = hostport[0]
  if len(hostport) == 2:
    port = int(hostport[1], 10)

  # Return the values.
  return username, password, hostname, port


def _urlparse_splitquery(url):
  """Parse the query portion of the url"""

  qpart = url.split("?", 1)
  if len(qpart) == 2:
    query = qpart[1]
  else:
    query = ""

  return qpart[0], query


def _urlparse_splitfragment(url):
  """Parse the query portion of the url"""

  fpart = url.split("#", 1)
  if len(fpart) == 2:
    fragment = fpart[1]
  else:
    fragment = ""

  return fpart[0], fragment

#end include urlparse.repy  
#begin include sockettimeout.repy
"""
<Author>
  Justin Cappos, Armon Dadgar
  This is a rewrite of the previous version by Richard Jordan

<Start Date>
  26 Aug 2009

<Description>
  A library that causes sockets to timeout if a recv / send call would
  block for more than an allotted amount of time.

"""


class SocketTimeoutError(Exception):
  """The socket timed out before receiving a response"""


class _timeout_socket():
  """
  <Purpose>
    Provides a socket like object which supports custom timeouts
    for send() and recv().
  """

  # Initialize with the socket object and a default timeout
  def __init__(self,socket,timeout=10, checkintv=0.1):
    """
    <Purpose>
      Initializes a timeout socket object.

    <Arguments>
      socket:
              A socket like object to wrap. Must support send,recv,close, and willblock.

      timeout:
              The default timeout for send() and recv().

      checkintv:
              How often socket operations (send,recv) should check if
              they can run. The smaller the interval the more time is
              spent busy waiting.
    """
    # Store the socket, timeout and check interval
    self.socket = socket
    self.timeout = timeout
    self.checkintv = checkintv


  # Allow changing the default timeout
  def settimeout(self,timeout=10):
    """
    <Purpose>
      Allows changing the default timeout interval.

    <Arguments>
      timeout:
              The new default timeout interval. Defaults to 10.
              Use 0 for no timeout. Given in seconds.

    """
    # Update
    self.timeout = timeout
  
  
  # Wrap willblock
  def willblock(self):
    """
    See socket.willblock()
    """
    return self.socket.willblock()


  # Wrap close
  def close(self):
    """
    See socket.close()
    """
    return self.socket.close()


  # Provide a recv() implementation
  def recv(self,bytes,timeout=None):
    """
    <Purpose>
      Allows receiving data from the socket object with a custom timeout.

    <Arguments>
      bytes:
          The maximum amount of bytes to read

      timeout:
          (Optional) Defaults to the value given at initialization, or by settimeout.
          If provided, the socket operation will timeout after this amount of time (sec).
          Use 0 for no timeout.

    <Exceptions>
      As with socket.recv(), socket.willblock(). Additionally, SocketTimeoutError is
      raised if the operation times out.

    <Returns>
      The data received from the socket.
    """
    # Set the timeout if None
    if timeout is None:
      timeout = self.timeout

    # Get the start time
    starttime = getruntime()

    # Block until we can read
    rblock, wblock = self.socket.willblock()
    while rblock:
      # Check if we should break
      if timeout > 0:
        # Get the elapsed time
        diff = getruntime() - starttime

        # Raise an exception
        if diff > timeout:
          raise SocketTimeoutError,"recv() timed out!"

      # Sleep
      sleep(self.checkintv)

      # Update rblock
      rblock, wblock = self.socket.willblock()

    # Do the recv
    return self.socket.recv(bytes)


  # Provide a send() implementation
  def send(self,data,timeout=None):
    """
    <Purpose>
      Allows sending data with the socket object with a custom timeout.

    <Arguments>
      data:
          The data to send

      timeout:
          (Optional) Defaults to the value given at initialization, or by settimeout.
          If provided, the socket operation will timeout after this amount of time (sec).
          Use 0 for no timeout.

    <Exceptions>
      As with socket.send(), socket.willblock(). Additionally, SocketTimeoutError is
      raised if the operation times out.

    <Returns>
      The number of bytes sent.
    """
    # Set the timeout if None
    if timeout is None:
      timeout = self.timeout

    # Get the start time
    starttime = getruntime()

    # Block until we can write
    rblock, wblock = self.socket.willblock()
    while wblock:
      # Check if we should break
      if timeout > 0:
        # Get the elapsed time
        diff = getruntime() - starttime

        # Raise an exception
        if diff > timeout:
          raise SocketTimeoutError,"send() timed out!"

      # Sleep
      sleep(self.checkintv)

      # Update rblock
      rblock, wblock = self.socket.willblock()

    # Do the recv
    return self.socket.send(data) 




def timeout_openconn(desthost, destport, localip=None, localport=None, timeout=5):
  """
  <Purpose> 
    Wrapper for openconn.   Very, very similar

  <Args>
    Same as Repy openconn

  <Exception>
    Raises the same exceptions as openconn.

  <Side Effects>
    Creates a socket object for the user

  <Returns>
    socket obj on success
  """

  realsocketlikeobject = openconn(desthost, destport, localip, localport, timeout)

  thissocketlikeobject = _timeout_socket(realsocketlikeobject, timeout)
  return thissocketlikeobject





def timeout_waitforconn(localip, localport, function, timeout=5):
  """
  <Purpose> 
    Wrapper for waitforconn.   Essentially does the same thing...

  <Args>
    Same as Repy waitforconn with the addition of a timeout argument.

  <Exceptions> 
    Same as Repy waitforconn

  <Side Effects>
    Sets up event listener which calls function on messages.

  <Returns>
    Handle to listener.
  """

  # We use a closure for the callback we pass to waitforconn so that we don't
  # have to map mainch's to callback functions or deal with potential race
  # conditions if we did maintain such a mapping. 
  def _timeout_waitforconn_callback(localip, localport, sockobj, ch, mainch):
    # 'timeout' is the free variable 'timeout' that was the argument to
    #  timeout_waitforconn.
    thissocketlikeobject = _timeout_socket(sockobj, timeout)

    # 'function' is the free variable 'function' that was the argument to
    #  timeout_waitforconn.
    return function(localip, localport, thissocketlikeobject, ch, mainch)

  return waitforconn(localip, localport, _timeout_waitforconn_callback)

  
  


# a wrapper for stopcomm
def timeout_stopcomm(commhandle):
  """
    Wrapper for stopcomm.   Does the same thing...
  """

  return stopcomm(commhandle)
  
    


#end include sockettimeout.repy
# used for hierarchy exception 
#begin include http_hierarchy_error.repy
"""
<Program Name>
  http_hierarchy_error.repy

<Started>
  Oct 05, 2009

<Author>
  Yafete Yemuru

<Purpose>
  provides a hierachy http error using status code including client and server errors
  classes.  
"""


'''
http hierarchy error exception classes

-> HttpError
   -> HttpRetrieveClientError
      -> HttpUserInputError
      -> HttpConnectionError

   -> HttpServerError
      -> HttpResponseError
         -> HttpHeaderError
            -> HttpHeaderReceivingError
            -> HttpHeaderFormatError
         -> HttpContentError
            -> HttpContentReceivingError
            -> HttpContentLengthError
       
   -> HttpStatuscodeError
     -> HttpError1xx
        -> followed by all http status code error number HttpError(number)
        
     -> HttpError2xx
        -> followed by all http status code error number HttpError(number)
        
     -> HttpError3xx
        -> followed by all http status code error number HttpError(number)

     -> HttpError4xx
        -> followed by all http status code error number HttpError(number)
        
     -> HttpError5xx
        -> followed by all http status code error number HttpError(number)

'''

class HttpError(Exception):
  pass

# raises an exception for http client error 
class HttpRetrieveClientError(HttpError):# extend HttpError 
  pass
class HttpUserInputError(HttpRetrieveClientError):
  pass
class HttpConnectionError(HttpRetrieveClientError):
  pass


# raises an exception for any http server failure  
class HttpServerError(HttpError):# extend HttpError 
  pass
class HttpResponseError(HttpServerError):
  pass
class HttpHeaderError(HttpResponseError):
  pass
class HttpHeaderReceivingError(HttpHeaderError):
  pass
class HttpHeaderFormatError(HttpHeaderError):
  pass
class HttpContentError(HttpResponseError):
  pass
class HttpContentReceivingError(HttpContentError):
  pass
class HttpContentLengthError(HttpContentError):
  pass


class HttpStatusCodeError(HttpError):# extend HttpError
  pass
class HttpError1xx(HttpStatusCodeError):
  pass
class HttpError100(HttpError1xx):
  pass
class HttpError101(HttpError1xx): 
  pass
class HttpError102(HttpError1xx): 
  pass


class HttpError2xx(HttpStatusCodeError):
  pass
class HttpError201(HttpError2xx): 
  pass
class HttpError202(HttpError2xx):   
  pass
class HttpError203(HttpError2xx): 
  pass
class HttpError204(HttpError2xx): 
  pass
class HttpError205(HttpError2xx): 
  pass
class HttpError206(HttpError2xx): 
  pass
class HttpError207(HttpError2xx): 
  pass
class HttpError226(HttpError2xx): 
  pass                 


class HttpError3xx(HttpStatusCodeError):
  pass
class HttpError300(HttpError3xx): 
  pass
class HttpError301(HttpError3xx): 
  pass
class HttpError302(HttpError3xx): 
  pass
class HttpError303(HttpError3xx): 
  pass
class HttpError304(HttpError3xx):
  pass
class HttpError305(HttpError3xx): 
  pass
class HttpError306(HttpError3xx): 
  pass
class HttpError307(HttpError3xx): 
  pass
                    

class HttpError4xx(HttpStatusCodeError):
  pass
class HttpError400(HttpError4xx):
  pass  
class HttpError401(HttpError4xx): 
  pass
class HttpError402(HttpError4xx): 
  pass
class HttpError403(HttpError4xx):
  pass  
class HttpError404(HttpError4xx): 
  pass
class HttpError405(HttpError4xx): 
  pass
class HttpError406(HttpError4xx): 
  pass
class HttpError407(HttpError4xx): 
  pass
class HttpError408(HttpError4xx): 
  pass
class HttpError409(HttpError4xx): 
  pass
class HttpError410(HttpError4xx): 
  pass
class HttpError411(HttpError4xx): 
  pass
class HttpError412(HttpError4xx): 
  pass
class HttpError413(HttpError4xx): 
  pass
class HttpError414(HttpError4xx): 
  pass
class HttpError415(HttpError4xx): 
  pass
class HttpError416(HttpError4xx): 
  pass
class HttpError417(HttpError4xx): 
  pass
class HttpError418(HttpError4xx): 
  pass
class HttpError422(HttpError4xx): 
  pass
class HttpError423(HttpError4xx): 
  pass
class HttpError424(HttpError4xx): 
  pass
class HttpError425(HttpError4xx): 
  pass
class HttpError426(HttpError4xx): 
  pass


class HttpError5xx(HttpStatusCodeError):
  pass
class HttpError500(HttpError5xx): 
  pass
class HttpError501(HttpError5xx): 
  pass
class HttpError502(HttpError5xx): 
  pass
class HttpError503(HttpError5xx): 
  pass
class HttpError504(HttpError5xx): 
  pass
class HttpError505(HttpError5xx): 
  pass
class HttpError506(HttpError5xx):
  pass  
class HttpError507(HttpError5xx):
  pass  
class HttpError510(HttpError5xx):
  pass

#end include http_hierarchy_error.repy





def registerhttpcallback(url, callbackfunc, httprequest_limit = 131072, httppost_limit = 2048):
  """
  <Purpose>
     Waits for a connection to the given url(host). Calls callbackfunc with a argument of http request
     dictionary up on success. 
  
     
  <Arguments>
     url:
           String of a http web server-URL 

     callbackfunc:
            The callbackfunc to be called. It can take up to three argument .
            First argument- The http request dictionary keys are as follows:
              http_command - for the http request method GET or POST
              http_version - which http version the client  used HTTP\1.1 or HTTP\1.0  
              path - the exact request path parsed 
              query - the exact request query parsed 
              posted_data - if there is any posted data returns None if there isnt one

              And all the http requests headers the client provided. eg. Content-Length: 22  
              will incude Content-Length as a key and 22 as a value

            Second argument - httprequest query; this returns a unencoded dictionary of the query
            Third argument - httprequest posted data; this returns a unencoded dictionary of the posted data

            RESTRICTIONS:
              -> Follow the http_hierarchy_error(HttpStatusCodeError)to raise an exception. eg. raise
                  HttpError404 for file not found
              -> To redirect raise HttpError301(url) or HttpError302(url). The url has to be valid.  
              -> server only excepts tuple type of [httpcontent, httpheader] where the httpcontent is a
                  string of the content intended to display. httpheader is a dictionary used only if you have a
                  extra header you want to add on the http response. 

     httprequest_limit:
            -> used to to limit the http request a client can make(default value set to 128kb or 131072 charactors)

     httppost_limit:
            -> used to to limit the http post a client can make(default value set to 2mb or 2048 charactors)     


  <Exceptions>
          HttpConnectionError-> if the server fails on waiting for a connection
          HttpUserInputError -> if server fails on making a connection to client(web browser)
          HttpServerError -> If server fails internally

          HttpError408 -> If client(web browser) takes to long to send request  
          HttpError413 -> If the http posted data length is too long
                       -> If the http request length is too long
          HttpError417 -> If there is the http request format problem
                       -> If the content length doesnt match the actual posted data length
          HttpError501 -> If the given http command is not supported or valid (supported 'GET' and 'POST')
          HttpError411 -> If the http command is POST and content length is not given
          HttpError500 -> If server fails internally on sending the http content OR HTTP header,sending error and
                       -> If the callback fucntion doesnt follow restrictions  
                       -> if the users input for url is not in correct format or unsuported
                          protocol(this program only supports Http)


  <Side Effects>
     None 

  <Returns>
     A handle to the listener. This can be used to stop the server from waiting for a connection.  
  """  
  def run_webserver(ip, port, sock, thiscommhandle, listencommhandle):
  # this function is defined inside the registerhttpcallback fuction so callback function name that is
  # given by a user is placed a call on when there is a connection. 
    try:
      # receive the client(web browser) request and return a list of the request
      client_request_lines = _registerhttpcallback_receive_client_request(sock, httprequest_limit)

      # check if the received request meets http requsest format standards and return a
      # dictionary of the http request headers. 
      httprequest_dictionary = _registerhttpcallback_make_httprequsest_dictionary(client_request_lines)    

      # check if there is posted data and add to the httprequest_dictionary with a key posted_data.
      # returns None if there isnt a posted data
      _registerhttpcallback_receive_httpposted_data(sock, httprequest_dictionary, httppost_limit)
      
      # get dictionary decode from the given query 
      httprequest_query = _registerhttpcallback_get_decode_dict(httprequest_dictionary, 'query')

      # get dictionary decode from the given post 
      httprequest_posted_data = _registerhttpcallback_get_decode_dict(httprequest_dictionary, 'posted_data')

      # place the call back callbackfunc with dictionary that includes http_command,
      # http_version, path, query, posted_data, and all the http requests headers
      webpage_content = callbackfunc(httprequest_dictionary, httprequest_query, httprequest_posted_data)
        
      # callback callbackfunc excecuted, send the processed dynamic web page data to client(web browser)
      _registerhttpcallback_send_httpresponse(sock, webpage_content)

      
    except HttpStatusCodeError, e:
      # send any error that occur during processing server to the client(web browser)
      _registerhttpcallback_send_httpformat_error(sock, e)
      
      
    except Exception, e:
      # if the program failed to catch an internal error raise an exception and send it to client(web browser)
      try:
        raise HttpError500('Server failed internally: ' + str(e))
      except Exception, e:
        _registerhttpcallback_send_httpformat_error(sock, e)



  
  # get the host and port from the given url to use for connection to listen on
  (host, port) = _registerhttpcallback_get_host_port(url)

  try:
    # waits for a client(web browser) to make a connetion and run the web server 
    listencommhandle = waitforconn(host, port, run_webserver)

  except Exception, e:
    # the waiting for a connection failed, stop waiting and raise an exception 
    raise HttpConnectionError('Web server failed on waiting for connection ' + str(e))

  else:
    # store the listencommhandle, to stop server if needed
    return listencommhandle








def stop_registerhttpcallback(handle):   
  """
    <Purpose>
          Deregister a callback for a commhandle. 

    <Arguments>
          commhandle:
              A commhandle as returned by registerhttpcallback.

    <Exceptions>
          None.

    <Side Effects>
          This has an undefined effect on a socket-like object if it is currently in use.

    <Returns>
          Returns True if commhandle was successfully closed, False if the handle cannot be closed 
  """
  #close the connection
  return stopcomm(handle)

   


  

def _registerhttpcallback_get_host_port(url):
  # get host and path from the given url
  try:
    # returns a dictionary of {scheme, netloc, path, quer, fragment, username, password, hostname and port} form the url
    urlparse = urlparse_urlsplit(url)  
  except Exception, e:
    raise HttpUserInputError('Server URL format error:' + str(e))
  else:
    # check if the given url is valid using the url parse 
    if urlparse['scheme'] != 'http':
      raise HttpUserInputError('The given protocol type isnt suported: Given ' + urlparse['scheme'])       
    if urlparse['hostname'] == None:
      raise HttpUserInputError('Server URL format error: host name is not given') 

    host = urlparse['hostname']
    
    # use default port 80 if the port isnt given
    if urlparse['port'] == None:
      port = 80
    else:
      # if given use the given port
      port = urlparse['port']

    return host, port



      
def _registerhttpcallback_receive_client_request(sock, httprequest_limit):
  # receive request from the client using the socket connection
  if not type(httprequest_limit) == int:
    # check if the given httprequest limit is valid
    raise HttpServerError('The given http request limit isnt int ' + str(e))
  
  
  # empty line is used as a signal for when the http request is done, and we set a
  # default request length limit to be 131072 character(128kb)
  client_request = _registerhttpcallback_receive_untilemptyline(sock, httprequest_limit)
        
  
  # http request format requires the request to be line by line
  # build a list of the received request split line by line to check the formating of the request
  client_request_lines = ''
  try: 
    # split the entire message line by line 
    client_request_lines = client_request.splitlines()
  except Exception, e:
    # raise an exception if the request doenst follow the http protocol format 
    raise HttpError417('Error on the http request format ' + str(e))
  
  # the http request has to be at least one line including the http header request
  if len(client_request_lines) == 0:
    raise HttpError417('The received request doesnt follow http protocol requirments: Given ' + client_request)

  # returns a list of client request
  return client_request_lines





def _registerhttpcallback_make_httprequsest_dictionary(client_request_lines):
  # builds up a dictionary from the received request or raises an exception if the
  # request format isnt http protocol. The dictionary also includes the http header request
  # parsed with custome keys (http_command - for http comand methed, path - parsed form
  # the request url, query - query string parsed form the request url, http_version -
  # for the http protocol version)
  
  httpheader_request = True
  httprequest_dictionary = {}
  
  for request_line in client_request_lines:  
    if httpheader_request:
      # acording to the http protocol format the first line is different because it is includes comand url and version

      # check if the http request is valid and parse the http request method, URL and http version
      (http_command, path, query, http_version) = _registerhttpcallback_httprequest_header_parse(request_line)

      # use custom names for the parsed data of the first request line and add to the dictionary 
      httprequest_dictionary['http_command'] = http_command
      httprequest_dictionary['http_version'] = http_version
      httprequest_dictionary['path'] = path
      httprequest_dictionary['query'] = query  

      # used to flag the for the upcoming lines, because they have stationary keys
      httpheader_request = False 
      
    elif request_line == '':
      # last line is empty line, return the http dictionary built so far
      return httprequest_dictionary  

    else:
      # the rest of the lines should be formated 'httpheader_key: httpheader_value'  eg.'Content-Length: 34'
      try:
        modified_request = request_line.split(': ')
      except Exception, e:
        raise HttpError417('Error on the http request format; Given: ' + request_line + 'in the request line ' + str(e))

      # raise an exception if the request line doesnt contain 2 contents for 'httpheader_key: httpheader_value' 
      if len(modified_request) != 2:
        raise HttpError417('Error on the http request format; Given: ' + request_line + 'in the request line')

      httprequest_key = modified_request[0]
      httprequest_value = modified_request[1]
      
      httprequest_dictionary[httprequest_key] = httprequest_value

  return httprequest_dictionary
  




def _registerhttpcallback_get_decode_dict(httprequest_dictionary , decode_type):
  # returns a decode dictionary of post or query depending up on the encoded style   

  # get the data from the request dictionary 
  data_to_decode = httprequest_dictionary[decode_type]
      
  if decode_type == 'posted_data':
    # inorder to check if the post is empty use None   
    empty_check = None    
  else:
    # inorder to check if the query is empty use empty string   
     empty_check = ''
        
  if data_to_decode != empty_check:
    try:
      # decode the given data depending up on the style it was encoded  
      return urllib_unquote_parameters(data_to_decode)

    except Exception, e:
      # raise an exception if the fails decoding the given data  
      raise HttpUserInputError('Invalid ' + decode_type + ' Raised ' + str(e) + ' on decoding')

  # if the data is empty return None 
  return None    




  
def _registerhttpcallback_httprequest_header_parse(http_header_request):
  # varifiy's if the http request header format is valid and returns the http command, path, query,
  # and http version parsed from the http header

  # http request header should include RequestMethod <url> HTTP<version> or RequestMethod HTTP<version>
  # and is located at the top of the http request
  try:
    http_command_url_version = http_header_request.split()
  except Exception, e:
    raise HttpError417('Http header request needs spacing in between: Given: ' + http_header_request + str(e))

  # Check that the first line at least contains 3  words: RequestMethod <url> HTTP<version>
  if len(http_command_url_version) >= 3: 
    url = http_command_url_version[1]
    http_version = http_command_url_version[2]
  
  else:
    # http request header cant have any more data than RequestMethod <url> HTTP<version> or RequestMethod HTTP<version>
    raise HttpError417('The request header should contain  RequestMethod <url> HTTP<version>, Given: ' + http_header_request)

  # check the http comand is valid or if its even suported(suported comands include GET and POST)
  if http_command_url_version[0] == 'GET' or http_command_url_version[0].lower() == 'post':
     http_command = http_command_url_version[0]
  else:
    raise HttpError501('The given http comand is not suported or valid. Given: ' + str(http_command_url_version[0]))
  

  # check the if the http version is valid
  if not http_version.startswith('HTTP'):
    raise HttpError417('Http header request version should start of with HTTP then <version>, Given: ' +  httpversion + ' as a http version') 

  # (query used to modify the dynamic page) http header includes the path and query, pasrse the given url to path and query 
  (path, query) = _registerhttpcallback_parse_httpheader_url(url)  

  return http_command, path, query, http_version 




def _registerhttpcallback_parse_httpheader_url(url):
  # parse out the query and path from the url
  path = ''
  query = ''

  # if url isnt given return empty strings  
  if url != '':
    # if url is given parse the query and path using url parse
    try:
     # returns a dictionary of {scheme, netloc, path, query, fragment, username,
     # password, hostname and port} parsing the url                      
      urlparse = urlparse_urlsplit(url)  
    except Exception, e:
      raise HttpError417('Http request given url doesnt meet the http protocol standards ' + str(e) + 'Given url: ' + url)

    # retrieve only the path and query 
    try:
      path = urlparse['path']
      query = urlparse['query']
    except Exception, e:
      raise HttpError417('Http request given url doesnt meet the http protocol standards ' + str(e) + 'Given url: ' + url)
        
    # if there is a url there has to be a path so raise an exception because the given url format is wrong 
    if path == '':
      raise HttpError417('Error on parsing the http request header url: Given ' + url)
    
  return path, query




def _registerhttpcallback_receive_httpposted_data(sock, httprequest_dictionary, httppoost_limit):
  # receive the posted data which sent right after the http request with a empty line
  # indicating the end of the posted data(this is if the http comand is only a POST)

  if not type(httppoost_limit) == int:
    # check if the given http post limit is valid
    raise HttpServerError('The given http post limit is not a int, given: ' + str(type(httppoost_limit)))

  # if the http comand method isnt post theres is no posted data
  posted_data = None

  # Bug pointed out by Albert Rafetseder: not all browsers send post with caps 
  if httprequest_dictionary['http_command'].lower() == 'post':
    # get the posted data length or raise an exception if not given 
    try:
      posted_data_length = int(httprequest_dictionary['Content-Length'])
    except Exception, e:   
      raise HttpError411('content length is required on a http POST comand')
    else:
      # Bug pointed out by Albert Rafetseder: post doesnt send a empty line after the posted data
      # recieve the posted data using the posted data length
      posted_data = _registerhttpcallback_receive_httppost(sock, posted_data_length, httppoost_limit)

    # check if there is a posted data and return it
    if len(posted_data) == 0:
      raise HttpError417('The request included a http POST comand with no data posted')
    
  # adds the posted data or None to the httprequest dictionary 
  httprequest_dictionary['posted_data'] = posted_data





def _registerhttpcallback_receive_httppost(sock, http_post_length, length_limit):
  # receives posted data from the given connection untill the given content length field matchs the received amount 
  total_recvd_post = ''
  
  while True:
    if len(total_recvd_post) == http_post_length:
      # if the content length matchs the received posted data return it 
      return total_recvd_post

    # raise an exception if the received posted data length is greater than the given http header content length   
    if len(total_recvd_post) > http_post_length:
      raise HttpError417('The http posted data didnt match the http content length header, given content length: ' + str(http_post_length) + ' while posted data length is ' + str(len(total_recvd_post)))

    # raise an exception if the total received length has exceeded the given length limit
    if len(total_recvd_post) > length_limit:                  
      raise HttpError413('The http posted data length exceeded length limit of ' + str(length_limit))

                       
    try:
      # receive one character at a time inorder to check for the empty line
      content = sock.recv(512)

    # catch any error that happens while receiving content             
    except SocketTimeoutError, e:
      raise HttpError408('The server timed out while waiting to receive the post data ' + str(e))
    except Exception, e: 
      raise HttpError500('Error while receiving request posted data ' + str(e))

    else:
      # if there was not receiving error, keep on adding the receieved content 
      total_recvd_post += content



  

def _registerhttpcallback_receive_untilemptyline(sock, length_limit):
  # receives data from socket connection until it a empty line or until the given
  # length limit is exceeded                      
  total_recvd_content = ''
  
  while True:
    # receive until a empty line (\n\n or \r\n\r\n because new line is different by computer) 
    if '\r\n\r\n' in total_recvd_content or '\n\n' in total_recvd_content:
      # found a empty line return the total received content
      return total_recvd_content.strip()

    # raise an exception if the total received length has exceeded the given length limit
    if len(total_recvd_content) > length_limit:                  
      raise HttpError413('The http request length exceeded the given length limit ' + str(length_limit))
                        
    try:
      # receive one character at a time inorder to check for the empty line
      content = sock.recv(1)

    # catch any error that happens while receiving content             
    except SocketTimeoutError, e:
      raise HttpError408('The server timed out while waiting to receive the request ' + str(e))
    except Exception, e: 
      raise HttpError500('Error while receiving http request ' + str(e))

    else:
      # if there was not receiving error, keep on adding the receieved content 
      total_recvd_content += content





def _registerhttpcallback_send_httpresponse(sock, callbackfunc_val):
  # sends a response to the client(web browser) with a ok http header and the http web page content
  if not type(callbackfunc_val) == list:
    raise HttpUserInputError('Callback func didnt return list, returned ' + str(type(callbackfunc_val)))

  try:
    webpage_content = callbackfunc_val[0]
    callbckfunc_httpheader = callbackfunc_val[1]
  except Exception, e:
    raise HttpUserInputError('Callback func returned data failed ' + str(e))

  # check the given web page content 
  if not type(webpage_content) == str:
    raise HttpUserInputError('Callback func didnt return str for the content, returned ' + str(type(webpage_content)))
  if len(webpage_content) == 0:
    raise HttpUserInputError('Callback func didnt return any content')
  
  
  # build the http ok response header 
  httpheader = 'HTTP/1.0 200 OK\n'
  httpheader += 'Content-Length: ' + str(len(webpage_content)) + '\n'
  #check if there is a given http header and add it to the response
  httpheader += _registerhttpcallback_parse_callbckfunc_httpheader(callbckfunc_httpheader)
    
  httpheader += 'Server: Seattle Testbed\n\n'

  # http header followed by http content and close the connection
  try:
    sock.send(httpheader)
    # sends data by chunk of 1024 charactors at a time
    _registerhttpcallback_sendbychunk(webpage_content, 1024, sock)
    sock.close() 
  except Exception, e:
    raise HttpConnectionError('server failed to send the http content ' + str(e))  





def _registerhttpcallback_sendbychunk(full_data, chunck_size, sock):
  # sends a given data to a socket connection by the chunk amount one at a time. 
  length_of_data = len(full_data)
  start = 0 
  end = chunck_size
  # used to signal when there is no more data left to parse by chunk size
  done = False
  
  while not done :
    if length_of_data <= end:
      # last end of data
      end = length_of_data
      done = True

    # parse the given data by the given chunk size and keep on sending by chunk bytes
    chuncked_data = full_data[start:end]

    try:
      sock.send(chuncked_data)  
    except Exception, e:
      raise Exception('faild on sending data: ' + str(e))
    else:
      # change start and end to send the next part of the data
      start = end
      end += chunck_size





def _registerhttpcallback_parse_callbckfunc_httpheader(callbckfunc_httpheader):
  # builds a http header from the given http callback func list
  if callbckfunc_httpheader == None:
    # if the http header isnt given return a empty string
    return ''
  elif not type(callbckfunc_httpheader) == dict:
    # raise an exception if the http header isnt dictionary
    raise HttpUserInputError('The given http header is not a dictionary, given: ' + str(type(callbckfunc_httpheader)))
  else: 
    # take the given key and val from the callbckfunc_httpheader dictionary and add them to the http header with
    # correct http format
    httpheaders = ''
    for key, val in callbckfunc_httpheader.items():
      # make simple checks on the key and val 
      if not type(key) == str:
        raise HttpUserInputError('The callback func given http header key isnt str given ' + str(type(key)))
      if not type(val) == str:
        raise HttpUserInputError('The callback func given http header value isnt str given ' + str( type(val)))
      if key == '' or val == '':
        # raise an exception if the key or value is a empty field
        raise HttpUserInputError('The callback func given empty http header feild of key or value')
      if key.capitalize() != key:
        raise HttpUserInputError('The callback func given http header key is not capitalized, given: ' + key)

      # add the key and value to the http header field
      httpheaders += key + ' : ' + val + '\n'  

    # return the string of the http header  
    return httpheaders

  



def _registerhttpcallback_send_httpformat_error(sock, e):
  # send  correct format http header with a  http content that displays detailed error msg and close connection 

  # using the httpstatuscode dictionary get the statuscode number and statuscode constant from the given httperror
  (statuscode_numb, client_error_msg, statuscode_constant) = _registerhttpcallback_get_http_statuscode(e)
  
  # build http body error msg to client(web browser)
  error_msg = client_error_msg

  # error content body
  httpcontent = '<html>'
  httpcontent += '<head><title>' + str(statuscode_numb) + ' ' + statuscode_constant + '</title></head>'
  httpcontent += '<body><h1>' + str(statuscode_numb) + ' ' + statuscode_constant + '</h1>'
  httpcontent += '<p>' + error_msg + '</p></body>'
  httpcontent += '</html>'
  # to end the error content
  httpcontent += '\n\n'
  
  # build the http header to send    
  httpheader = 'HTTP/1.0 ' + str(statuscode_numb)  + ' ' + statuscode_constant + '\n'

  # for redirect add the location of the redirection to the http header    
  if statuscode_numb == 301 or statuscode_numb == 302:
    if client_error_msg == '':
      raise HttpUserInputError('Internal server error: callback func client should put the location on raising redirect')
    elif not client_error_msg.startswith('http://'):
      raise HttpUserInputError('Internal server error: calback func client redirect is invalid, Given: ' + client_error_msg)
    else:
      httpheader += 'Location: ' + str(client_error_msg) + '\n'
  
  # finish up the http header
  httpheader += 'Content-Length: ' + str(len(httpcontent)) + '\n'
  httpheader += 'Server: Seattle Testbed\n\n'
  
  # send the http response header and body to the client(web browser) and close connection
  try:
    sock.send(httpheader)
    sock.send(httpcontent)
    sock.close()
  except Exception, e:
    raise HttpConnectionError('server failed internally on send http error ' + str(statuscode_numb) + ' ' + statuscode_constant + ' ' + error_msg + ' Raised' + str(e)) 




def _registerhttpcallback_get_http_statuscode(e):
  # retrieves the status code number and constant given a exception class 
  
  # httpstatus code dictionary with the statuscode constant
  httpstatuscode_dict = {
      HttpError100: (100, 'Continue'),
      HttpError101: (101, 'Switching Protocols'),
      HttpError102: (102, 'Processing'),
      HttpError201: (201 ,'Created'),
      HttpError202: (202, 'Accepted'),  
      HttpError203: (203, 'Non-Authoritative Information'),
      HttpError204: (204, 'No Content'),
      HttpError205: (205, 'Reset Content'),
      HttpError206: (206, 'Partial Content'),
      HttpError207: (207, 'Multi-Status'),
      HttpError226: (226, 'IM Used'),
      HttpError300: (300, 'Multiple Choices'),
      HttpError301: (301, 'Moved Permanently'),
      HttpError302: (302, 'Found'),
      HttpError303: (303, 'See Other'),
      HttpError304: (304, 'Not Modified'),
      HttpError305: (305, 'Use Proxy'),
      HttpError306: (306, 'Unused'),
      HttpError307: (307, 'Temporary Redirect'),
      HttpError400: (400, 'Bad Request'),
      HttpError401: (401, 'Unauthorized'),
      HttpError402: (402, 'Payment Required'),
      HttpError403: (403, 'Forbidden'),
      HttpError404: (404, 'Not Found'),
      HttpError405: (405, 'Method Not Allowed'),
      HttpError406: (406, 'Not Acceptable'),
      HttpError407: (407, 'Proxy Authentication Required'),
      HttpError408: (408, 'Request Timeout'),
      HttpError409: (409, 'Conflict'),
      HttpError410: (410, 'Gone'),
      HttpError411: (411, 'Length Required'),
      HttpError412: (412, 'Precondition Failed'),
      HttpError413: (413, 'Request Entity Too Large'),
      HttpError414: (414, 'Request-URI Too Long'),
      HttpError415: (415, 'Unsupported Media Type'),
      HttpError416: (416, 'Requested Range Not Satisfiable'),
      HttpError417: (417, 'Expectation Failed'),
      HttpError418: (418, 'Im a teapot'),
      HttpError422: (422, 'Unprocessable Entity'),
      HttpError423: (423, 'Locked'),
      HttpError424: (424, 'Failed Dependency'),
      HttpError425: (425, 'Unordered Collection'),
      HttpError426: (426, 'Upgrade Required'),
      HttpError500: (500, 'Internal Server Error'),
      HttpError501: (501, 'Not Implemented'),
      HttpError502: (502, 'Bad Gateway'),
      HttpError503: (503, 'Service Unavailable'),
      HttpError504: (504, 'Gateway Timeout'),
      HttpError505: (505, 'HTTP Version Not Supported'),
      HttpError506: (506, 'Variant Also Negotiates'),
      HttpError507: (507, 'Insufficient Storage'),
      HttpError510: (510, 'Not Extended')}
  
  # retrieves the status number and constant from the given exception class using the dictionary 
  try:
    (statuscode_numb, statuscode_constant) = httpstatuscode_dict[type(e)]
  except Exception, e:
    raise HttpServerError('Internal error on generating error msg: ' + str(e))

  # get any extra error msg that the callback fucntion raised 
  client_error_msg = str(e)

  # return what is retrieved
  return statuscode_numb, client_error_msg, statuscode_constant





#end include registerhttpcallback.repy


#webserver functionality based off the old webserver
def callbackfunc(request_dictionary, httpreqquery, posteddata):
  
  msg = request_dictionary['path']
  if msg == 400:
    response = '<h1>400 Bad Request</h1>'

  elif msg == 414:
    response = '<h1>414 URI Too Long</h1>'

  else:
    files = listdir()

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
          except:
            response = '<h1> File could not be opened or read</h1>'
      if(found == 0):
        response = '<h1>File Not Found</h1>'
 
  return [response, None]

def main():
  ip = getmyip()
  url = 'http://' + ip + ':12345'
  registerhttpcallback(url, callbackfunc)
  while 1 == 1:
    sleep(1000)
  
  
if callfunc == "initialize":
  main()
