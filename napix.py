#!/usr/bin/env python
# 
# Copyright (C) 2010 Bartosz SKOWRON.
#
# Author: Bartosz SKOWRON <getxsick at gmail dot com>
#
# convert() is based on reversed napi 0.16.3.1 application without any license
#
# Requirements: 7z (p7zip-full on Debian system)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import hashlib, urllib
import sys, os, os.path
from shutil import copy2 as copyfile
from glob import glob
from optparse import OptionParser
from tempfile import NamedTemporaryFile

FILE_FORMATS = ['avi', 'mpg', 'mp4', 'rmvb',]

def convert(z):
    idx = [ 0xe, 0x3,  0x6, 0x8, 0x2 ]
    mul = [   2,   2,    5,   4,   3 ]
    add = [   0, 0xd, 0x10, 0xb, 0x5 ]

    b = []
    for i in xrange(len(idx)):
        a = add[i]
        m = mul[i]
        i = idx[i]

        t = a + int(z[i], 16)
        v = int(z[t:t+2], 16)
        b.append( ("%x" % (v*m))[-1] )

    return ''.join(b)

def split_ext(filename):
    """
    Return tuple of filename and extenstion.
    """
    l = filename.rpartition('.')
    return (l[0], l[2])

def gen_url(fname):
    hashsum = hashlib.md5();
    hashsum.update(open(fname).read(10485760))
    hexdigest = hashsum.hexdigest()

    url = "http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s" % (
            hexdigest, convert(hexdigest), os.name)
    return url

def get_subtitle(fname):
    url = gen_url(fname)
    f_archive7z = NamedTemporaryFile(delete=False)
    f_archive7z.write(urllib.urlopen(url).read())
    f_archive7z.close() # flush buffers
    txtpath=split_ext(fname)[0] + '.txt'

    f_newtxt = NamedTemporaryFile(delete=False)
    f_newtxt.close()

    print os.path.basename(fname),

    if os.path.exists(txtpath):
        hash_old = hashlib.md5()
        hash_old.update(open(txtpath).read())

    # XXX Use this when resolved - http://bugs.python.org/issue5689
    if os.system("7z x -y -so -piBlm8NTigvru0Jr0 %s 2>/dev/null >\"%s\"" % (
                                            f_archive7z.name, f_newtxt.name)):
        print " : [ FAIL ]"
    elif os.path.exists(txtpath):
        hash_new = hashlib.md5()
        hash_new.update(open(f_newtxt.name).read())
        if hash_old.hexdigest() != hash_new.hexdigest():
            os.rename(txtpath, txtpath+".bak")
            print " : [ OK - backup ]"
        else:
            print " : [ OK - exists ]"
    else:
        print " : [ OK ]"
    copyfile(f_newtxt.name, txtpath)

    os.remove(f_archive7z.name)
    os.remove(f_newtxt.name)

def get_files(dirpath):
    def add_file(l, directory, files):
        for f in files:
            path = os.path.join(directory, f)
            if os.path.isfile(path) and split_ext(f)[1].lower() in FILE_FORMATS:
                l.append(path)

    l = []
    if dirpath and os.path.isdir(dirpath):
        os.path.walk(dirpath, add_file, l)
    else:
        print >>sys.stderr, "%s : Dir not found" % dirpath

    return l

if __name__=='__main__':
    usage = "usage: %prog [options] FILE1 FILE2 ..."
    parser = OptionParser(usage)
    parser.add_option("-e", "--ext", dest="ext", metavar="EXT1,EXT2",
                      help="follow up additional extensions")
    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    # add new extesions to the list
    if options.ext:
        l = options.ext.split(',')
        FILE_FORMATS.extend([ x.lower() for x in l ])

    # detect dirs
    filelist = []
    for f in args:
        if os.path.isdir(f):
            filelist.extend(get_files(f))
        else:
            filelist.append(f)

    # main action
    for f in filelist:
        if os.path.isfile(f):
            get_subtitle(f)
        else:
            print >>sys.stderr, "%s : File not found or directory" % f
