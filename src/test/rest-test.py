#!/usr/bin/env python2.7
#
# Test script for python-crucible
#
# This script tests a few functions from python-crucible.
# Attention: It adds a comment to a test item!
#
# You need to create Cfg.py with the configuration data (expecially the
# password). See below in the section "Configuration" for a template.

import sys
import json
# if you don't install python-crucible, you can add its directory to the search path
sys.path.append('./python-crucible/src/modules')
import crucible

### Configuration ############################################################

import Cfg

# Template for Cfg.py
# --------------------------------------------------------------------------
# # Configuration
# #
# #
#
# # URL uf the Crucible installation (without trailing '/')
# BaseUrl = 'https://my.crucible.server/crucible'
# # User
# User    = 'username'
# # Password
# Pass    = 'secretpassword'
# # review id to be used for the tests
# Review  = 'review-1'
# --------------------------------------------------------------------------

### Main #####################################################################
# script started from console
if __name__ == "__main__":
  # Initialize, login
  C = crucible.Api(Cfg.BaseUrl);
  C.login(Cfg.User, Cfg.Pass)

  # Get all open reviews for everyone in all projects
#  R = C.getReviews('allOpenReviews')
#  print R

  # Get all open reviews created by the current user
#  R = C.getReviews('open')
#  print json.dumps(R, indent=2)

  # Get all open reviews of a specific project, but should not be used
#  R = C.getReviews('?project=RXS8160')
#  print json.dumps(R, indent=2)

  # Get information for a single review
  R = C.getReview(Cfg.Review)
  rid = R.data['permaId']['id']
  print "review perma id = '"+rid+"'"
  print json.dumps(R.data, indent=2)

  # Get all review items (files) of that review
  R = C.getReviewItems(rid)
#  print json.dumps(R, indent=2)
  for item in R:
    riid = item['permId']['id']
    path = item['toPath']
    rev  = item['toRevision']
    print riid+": " + path + ' revision ' + rev
  
  # Get all comments for that review item
  # use last "riid"
  R = C.getReviewItemComments(rid, riid, render=True)
#  print json.dumps(R, indent=2)
  for item in R:
    cid   = item['permaId']
    lines = item['toLineRange']  # either "3" or "5-12"
    msg   = item['message']
    print '%s: %s: %s' % (cid, lines, msg)
  
  # Add a comment to that review item
  R = C.addReviewItemComment(rid, riid, 'Automatic test comment', 16)
  print json.dumps(R, indent=2)
  cid   = R['permaId']
  lines = R['toLineRange']  # either "3" or "5-12"
  msg   = R['message']
  riid  = R['reviewItemId']['id']
  print "Created new comment with id %s to review item %s line(s) %s: %s" % (cid, riid, lines, msg)

