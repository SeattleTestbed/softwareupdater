"""
<Program>
  test_rsync.py
  
<Author>
  Brent Couvrette

<Start Date>
  October 16, 2008

<Purpose>
  Test the rsync behavior in a varity of different ways.

  Note that while this can be used alone, it is mostly meant to be run from
  within test_runupdate.py.  See test_updater.py for more details.

<Usage>
  python test_rsync.py <testtype> <softwareurl>

  Test types:
  -u <filename1 filename2 ... >    Test will assert that all of the given
                                   filenames were updated correctly.
  -x	                  Test will assert that no updates have been made
  -e                      Test will assert that there was a proper
                          Exception thrown
  												
  Note, it is assumed that the files to be updated are all currently in the
  current directory
"""

import softwareupdater
import sys
import tempfile
import shutil
import glob
import os
import traceback

help = """Usage:
python test_rsync.py <testtype> <softwareurl>

Test types:
-u <filename1 filename2 ... >    Test will assert that all of the given 
                                 filenames were updated correctly.
-x                               Test will assert that no updates have been
                                 made
-e                               Test will assert that there was a proper
                                 Exception thrown

"""

def test_rsync(testtype, softwareurl, chgFile=None):
  """
  <Purpose>
    Does the actual rsync test of the given type, at the given softwareurl,
    and with the given expected update list (empty by default).

  <Arguments>
    testtype - The type of test to be performed.  See usage in this module's
               docstring for details.
    softwareurl - The location to rsync with.
    chgFile - A list of files to be updated.  Only used with the -u option,
              it defaults to empty.

  <Exceptions>
    None

  <Side Effects>
    None

  <Returns>
    A string indicating the results of the test.
  """
  
  if chgFile is None:
    chgFile = []

  # Start building the standard test output that will be printed.
  testout = 'Test type: ' + str(testtype)

  chgTime = {}
  
  # To determine whether or not something changed, check the last
  # modification time befor and after the update.
  # Here we get the times before the update.
  if testtype == '-x' or testtype == '-u' or testtype == '-e':
    # We may want to refine this to only include relavent files.
    # for now it checks against all files (but not directories) in
    # the current directory.
    for upfile in glob.glob('*'):
      # ignore directories...
      if os.path.isdir(upfile):
        continue

      # put the last modification time into the proper place in
      # the chgTime list
      chgTime[upfile] = os.stat(upfile).st_mtime


  testout = testout + ' URL: ' + softwareurl  

  # where I'll put temp files...
  tempdir = tempfile.mkdtemp()+"/"

  success = ''  
  updatedlist = []
  
  # run rsync
  try:
    updatedlist = softwareupdater.do_rsync(softwareurl, "./",tempdir)
  # Read the test's output
  except Exception, e:
    # If we wanted an error to happen, then this means
    # success!
    if testtype != '-e':
      type, value, tb = sys.exc_info()
      success = 'Unexpected Rsync Exception :(\n'
      for line in traceback.format_exception(type, value, tb):
        success = success + line
      
  finally:
    shutil.rmtree(tempdir)

  # The specified files should have been updated, and no others.
  if testtype == '-u':
    # First run through the updated list and make sure all the
    # right files are there.
    for upfile in chgFile:
      # ignore directories...
      if os.path.isdir(upfile):
        continue

      if updatedlist and upfile in updatedlist:
        updatedlist.remove(upfile)
      else:
        success = success + upfile + ' was supposed to be updated, but was not included in the updatedlist\n'

    # Make sure the right files were the only files in the updated list
    if updatedlist:
      if len(updatedlist) != 0:
        success = success + 'Some files were unexpectedly put on the updated list ' + str(updatedlist) + '\n'

    # We may want to refine this to only include relavent files.
    # for now it checks against all files in the current directory (but not
    # directories).
    for upfile in glob.glob('*'):
      # ignore directories...
      if os.path.isdir(upfile):
        continue

      if upfile in chgFile:
        # If it should have been updated, then its last mod time should
        # also be updated
        if chgTime[upfile] >= os.stat(upfile).st_mtime:
          success = success + upfile + " should have been updated, but wasn't\n"
      else:		
        # If it wasn't supposed to be updated, then its last mod time
        # should not be changed.
        if chgTime[upfile] != os.stat(upfile).st_mtime:
          success = success + upfile + " was unexpectedly updated!\n"

    if success == '':
      testout = testout + '    [ PASS ]'
    else:
      testout = testout + '    [ FAIL ]'

  # No updates should have happened
  if testtype == '-x' or testtype == '-e':
    # We may want to refine this to only include relavent files.
    # for now it checks against all files in the current directory (but not
    # directories).
    for upfile in glob.glob('*'):
      # ignore directories...
      if os.path.isdir(upfile):
        continue

      # make sure the modification time is unchanged
      if chgTime[upfile] != os.stat(upfile).st_mtime:
        success = success + upfile + ' was unexpectedly updated!\n'

    # if we haven't written any errors to success, we pass.
    if success == '':
      testout = testout + '    [ PASS ]'
    else:
      testout = testout + '    [ FAIL ]'

  return testout + '\n' + success



def main():
  # Parse the args
  if len(sys.argv) < 3:
    print 'Invalid number of arguments'
    print help
    sys.exit(1)

  testtype = sys.argv[1]
  
  if testtype != '-u' and testtype != '-x' and testtype != '-e':
    print 'Invalid test type!'
    print help

  sys.argv = sys.argv[1:]

  chgFile = []

  # Get all the file names if the test type is -u
  if testtype == '-u':
    # we are done when sys.argv[1] is the last value, meaning
    # it is the software url.
    while len(sys.argv) != 2:
      # put the next file that should change into 
      # the chgFile list
      chgFile.append(sys.argv[1])
      sys.argv = sys.argv[1:]

  # set the url that we will try to rsync with	
  softwareurl = sys.argv[1]

  print test_rsync(testtype, softwareurl, chgFile)



if __name__ == '__main__':
  main()
