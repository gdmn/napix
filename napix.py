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
import itertools
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

def gen_url(fname):
    hashsum = hashlib.md5();
    hashsum.update(open(fname).read(10485760))
    hexdigest = hashsum.hexdigest()

    url = "http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s" % (
            hexdigest, convert(hexdigest), os.name)
    return url

def get_subtitle(fname):
    url = gen_url(fname)
    f = NamedTemporaryFile(delete=False)
    f.write(urllib.urlopen(url).read())
    f.close() # flush buffers
    name=fname[:-3] + 'txt'

    print os.path.basename(fname),
    if os.system("/usr/bin/7z x -y -so -piBlm8NTigvru0Jr0 %s 2>/dev/null >\"%s\"" % (f.name, name)):
        print " : [ FAIL ]"
        os.remove(name)
    else:
        print " : [ OK ]"
    os.remove(f.name)

def get_files(dirpath):
    l = []
    if dirpath:
        if os.path.exists(dirpath):
            for ext in FILE_FORMATS:
                l.extend(glob(os.path.join(dirpath, '*.%s' % ext)))
        else:
            print >>sys.stderr, "%s : Dir not found" % dirpath
    return l

if __name__=='__main__':
    usage = "usage: %prog [options] FILE1 FILE2 ..."
    parser = OptionParser(usage)
    parser.add_option("-d", "--dir", dest="dir", #default="",
                      help="directory with movies", metavar="DIR")
    parser.add_option("-e", "--ext", dest="ext", metavar="EXT1,EXT2",
                      help="follow up additional extensions")
    (options, args) = parser.parse_args()

    if not (args or options.dir):
        parser.print_help()
        sys.exit(1)

    # add new extesions to the list
    if options.ext:
        l = options.ext.split(',')
        FILE_FORMATS.extend(l)

    l = get_files(options.dir)
    for f in itertools.chain(l, args):
        if os.path.isfile(f):
            get_subtitle(f)
        else:
            print >>sys.stderr, "%s : File not found or directory" % f
