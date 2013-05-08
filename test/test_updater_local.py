"""
<Program>
  test_updater_local.py

<Author>
  Brent Couvrette

<Start Date>
  February 14, 2009

<Purpose>
  Runs all the softwareupdater tests locally using the webserver written in 
  repy.

<Usage>
  Requires files from trunk/assignments/webserver/ and 
  trunk/softwareupdater/test/ as well as a normal preparetest.  Also, there
  cannot be another instance of softwareupdater.py running, or the restart
  tests will fail.  Note that when running these tests on Windows, ps cannot 
  be used to check process status.  You will have to do this yourself in the
  task manager.
  
  Each rsync unit test has 3 lines of output.  The first is the webserver
  telling you the ip address it is listening on (this should be the address
  of the local machine).  The second line is the local folder that the 
  webserver is serving.  The third line notes the type of test, the url being
  passed to rsync, and whether or not the test passed.
  
  For the restart test, initially there should be only one softwareupdater
  running.  The return code that is printed next should be 10, and there
  should still be only one softwareupdater running after this.  The finally,
  there should be output saying "Second update a success!".
  
<Side Effects>
  If everything is successful, there will be an instance of softwareupdater.py
  and nmmain.py running when this script completes.  It is non-trivial to clean
  this up here, because we do not directly start these processes.

<Inner Workings>
  To start, the tests need to create folders that the softwareupdater will be
  able to try to get updates from.  The softwareupdater itself must also be
  modified so that it is looking for the correct update site and has the
  correct testing key.  Also, once the folders are created, nminit.py needs to
  do its thing so the softwareupdater can do its service logging.  All these
  things are done by the create_folders function in test_updater.  The folders
  are created via tempfile.mkdtemp so they can be easily cleaned away when the
  tests are done running.  Once we have everything set up properly, we can then
  run the tests.

  First we start by running the rsync only tests.  These tests just test the 
  do_rsync method of the softwareupdater by importing softwareupdater and
  calling it manually.  Before the start of each test we must start a 
  webserver that will serve files from whatever folder has the appropriate 
  files for the current test.  Because the webserver is restricted to only
  serving files in its current directory, we cannot just run one webserver
  that serves files for all of the tests.  Once the test is done, we need to
  kill the webserver as well, so there won't be any conflicts when starting
  up the next one.

  Once the rsync tests are done running, we run the tests that make sure the
  whole softwareupdater is capable of running, updating, and restarting itself
  if need be.  For this we first point it at an update that will change its
  key, then at an update that requires that new key, but just updates the
  node manager.
"""

from repyportability import *

import test_updater
import subprocess
import os
import signal
import glob
import sys
import shutil
import time
import urllib
import tempfile
import traceback
# To determine the OS type
import nonportable


if nonportable.ostype == 'Windows':
  # We need to be able to kill the webserver.
  import windows_api



def runRsyncTest(testtype, updatefolder, otherargs=None):
  """
  <Purpose>
    Runs a test on the rsync-like portion of the software updater.  It first
    starts the webserver in the given folder, then runs the test, then kills
    the webserver.
  <Arguments>
    testtype - The type of rsync test to run.  Test types are reproduced here:
        -u <filename1 filename2 ... >    Test will assert that all of the given 
                                         filenames were updated correctly.
        -x                     Test will assert that no updates have been made
        -e                     Test will assert that there was a proper
                               Exception thrown

    updatefolder - The folder to run the webserver from (it should be one of
                   the directories created by test_updater.py).
    otherargs - The list of file names necesary for the -u test type.  Should
        be empty (the default) for any other test type.
  <Exceptions>
    None?
  <Side Effects>
    There will be an attempted update to the current folder.  If the update is
    successfull, the files in the current folder will match those in the given
    update folder.
  <Return>
    None
  """

  if otherargs is None:
    otherargs = []

  # Can't do this import until nminit is run, which has to happen at the end
  # of test_updater.main().
  import test_rsync
  
  # Initialize the update url to just be the ip address of this machine.
  ip = getmyip()
  updateurl = 'http://' + ip + ':12345/'
  
  webserver = run_webserver(updatefolder)
  print updatefolder
  # Run the test
  rsync = subprocess.Popen([sys.executable, 'test_rsync.py', testtype]+otherargs+[updateurl], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

  # Get the output
  theout = rsync.communicate()[0]

  # Print the output
  print theout
  kill_webserver(webserver.pid, updateurl)



def kill_webserver(pid, url):
  """
  <Purpose>
    When killing the webserver, we want to make sure it is no longer serving
    files before declaring it officially dead.  This method ensures that this
    happens.
  <Arguments>
    pid - The pid of the webserver
    url - The url the webserver can be accessed at.  Queried to ensure the 
          webserver is no longer serving data.
  <Exceptions>
    Exception if the pid is invalid
  <Side Effects>
    The given pid is killed.
  <Returns>
    None
  """
  if nonportable.ostype == 'Windows':
    windows_api.kill_process(pid)
  else:
    os.kill(pid, signal.SIGKILL)

  # We need to make sure the webserver is stopped up before returning.  Waiting
  # an arbitrary amount of time is just asking for strange and inconsistent
  # errors, so I will actually query the web server until it fails.  However,
  # to prevent an infinite loop, I will limit the waiting to 1 minute.  What
  # else can we do if it doesn't die other than just raising an exception?
  for junk in xrange(60):
    try:
      # If we can successfully retrieve the url, we aren't ready.
      urllib.urlretrieve(url)
    except Exception:
      # We are done when it fails!
      return
    
    time.sleep(1)

  # If it didn't die within the 60 seconds it was given, it probably won't die
  # any time soon, so we will raise an exception and to exit ourselves.
  raise Exception("Could not kill the webserver.   pid == " + str(pid) + \
      " :: url == " + str(url))


def run_webserver(path):
  """
  <Purpose>
    Runs the repy webserver, assuming the server and its restrictions file 
    are in the current directory.  The webserver will serve files only from
    the given directory, not subdirectories of this directory.
  <Arguments>
    path - The directory from which files will be served.
  <Exceptions>
    None
  <Side Effects>
    A webserver is started serving files from the given directory.
  <Return>
    The process handle for the webserver.
  """

  webserver = subprocess.Popen([sys.executable, 'repy.py', '--cwd', path,
      'webserver_restrictions.test', 'webserver.repy'], 
      stderr=subprocess.PIPE) 
      
  
  # We need to make sure the webserver starts up before returning.  Waiting
  # an arbitrary amount of time is just asking for strange and inconsistent
  # errors, so I will actually query the web server until it works.  However,
  # to prevent an infinite loop, I will limit the waiting to 1 minute.  If 
  # the webserver has not started by this time, it is probably safe to say
  # it won't start.  In this case we will raise an exception indicating this.
  
  # Initialize the update url to just be the ip address of this machine.
  ip = getmyip()
  updateurl = 'http://' + ip + ':12345/'
  
  for junk in xrange(60):
    try:
      # If we can successfully retrieve the url, we are ready.
      urllib.urlretrieve(updateurl)
      break
    except Exception:
      time.sleep(1)

  if webserver.poll() != None:
    # The webserver has exited!!
    raise Exception('Webserver exitted with code ' + str(webserver.poll()))

  return webserver



def main():
  # Initialize the update url to just be the ip address of this machine.
  ip = getmyip()
  updateurl = 'http://' + ip + ':12345/'
  
  if len(sys.argv) == 1:
    sys.argv.append(updateurl)
  else:
    sys.argv[1] = updateurl
    
  # Create a temp directory to serve the updates from that we can 
  # automatically clean up when we are done.
  tmpserver = tempfile.mkdtemp()
  try:
    test_updater.create_folders(tmpserver)
  
  ############################
  # Run the rsync only tests #
  ############################

    # Run the noup test (Nothing should fail, nothing should be updated)
    runRsyncTest('-x', tmpserver + '/noup/')

    # Run the wronghash test(There should be an RsyncError, and no updates)
    runRsyncTest('-e', tmpserver + '/wronghash/')
  
    # Run the badkeysig test (There should be no updates)
    runRsyncTest('-x', tmpserver + '/badkeysig/')

    # Run the corruptmeta test (there should be an RsyncError, and no updates)
    runRsyncTest('-e', tmpserver + '/corruptmeta/')

    # Run the updatenmmain test (only nmmain should get updated)
    runRsyncTest('-u', tmpserver + '/updatenmmain/', ['nmmain.py', 'metainfo'])
  
    # Run an update that should get us into a state where the softwareupdater has
    # a different key than what the metainfo is signed with.  The next test will
    # ensure that our method of dealing with this situation works.
    runRsyncTest('-u', tmpserver + '/updater/', ['softwareupdater.py', 'metainfo'])
  
    # Run an update that should successfully update from the strange state from
    # the previous test.
    runRsyncTest('-u', tmpserver + '/updater_new/', ['nmmain.py', 'metainfo'])

  #####################################
  # Finished running rsync only tests #
  #####################################

    # Copy back everything from noup so the restart tests start with a 
    # clean slate.
    for originalfile in glob.glob(tmpserver + '/noup/*'):
      shutil.copy(originalfile, os.path.basename(originalfile))
     
      
  ##################################
  # Software updater restart tests #
  ##################################
    # Start the web server for the first update
    webserver = run_webserver(tmpserver + '/updater/')

    # Keep track of whether ps is there (it isn't on Windows)
    no_ps = False
  
    if nonportable.ostype == 'Windows':
      # If we are running on windows, disable the ps calls.
      no_ps = True
   
    # We use bsd syntax for the ps command because it works on bsd, darwin, and linux.
    # (bsd syntax means basically no dash before the options and maybe some different
    # letters used for the options.)
    # The 'ww' is to make sure that bsd doesn't limit the column length of output.
    # The 'ax' shows all processes.
    # The 'u' shows the username rather than user id running the process.
    pscommand = 'ps auxww'
 
    updateprocess = subprocess.Popen([sys.executable, 'softwareupdater.py'])
    if not no_ps:
      # Only do the ps check if ps is available
      ps = subprocess.Popen(pscommand + ' | grep "softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
      psout = ps.communicate()[0]
      print 'Initial ps out:'
      print psout
      if psout == '':
        print 'Failure to start initially'

    # Wait for 6 minutes for the update to happen and the
    # process to die. This was increased from 2 minutes because the test was failing
    # on testbed-mac. Possibly with only 2 minutes allowed it wasn't accounting
    # for the time it would take to do the actual update, only the time it would
    # take for the update to start. These tests are poorly organized, so I don't
    # say that with full confidence.
    for junk in range(360):
      if updateprocess.poll() != None:
        break
      time.sleep(1)

    ret = updateprocess.returncode
    if ret != 10:
      if ret == None:
        raise Exception("First software updater never died.")
      elif ret == 55:
        raise Exception("Software updater failed to get the process lock.")
      elif ret == 1:
        raise Exception("Softwareupdater failed with an uncaught exception. \n\
            See end of softwareupdater.old in v2 for details.")
      else:
        raise Exception("Unknown return code from the software updater (" + 
            str(ret) + ")")
    else:
      print "Old softwareupdater returned correctly"
      if not no_ps:
        # Only do the ps check if ps is available
        ps = subprocess.Popen(pscommand + ' | grep "softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
        psout = ps.communicate()[0]
        print 'After ps out:'
        print psout
        if psout == '':
          print 'New updater failed to start!'
        else:
          print 'softwareupdater restart success!'

    # We need to kill the webserver serving from /updater, and start one serving
    # from updater_new
    kill_webserver(webserver.pid, updateurl)
    webserver = run_webserver(tmpserver + '/updater_new/')

    print "Waiting 2 minutes for the second update to happen"
    # Wait 2 minutes for the second update to happen.
    # Is there a way to get a handle for the new softwareupdater?
    time.sleep(120)

    # If nmmain's version has been updated, the second update was a success!
    nmmainfile = file('nmmain.py', 'r')
    nmmaindata = nmmainfile.read()
    nmmainfile.close()
    if 'version = "1234"' in nmmaindata:
      print 'Second update a success!'
    else:
      print 'Second update failed to happen within 2 minutes'
  
    # Kill the webserver again now that we are all done with it.
    kill_webserver(webserver.pid, updateurl)

  ######################################
  # End Software updater restart tests #
  ######################################
  except:
    traceback.print_exc()
  finally:
    # Clean up the temporary server directory.
    # This throws an exception on Windows if a file is still in use (for example,
    # if the webserver started in a test couldn't be shut down).
    shutil.rmtree(tmpserver) 
  

if __name__ == "__main__":
  main()
