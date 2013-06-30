#!/usr/bin/env python

from httplib import HTTPSConnection
from HTMLParser import HTMLParser
from urllib import urlretrieve
from urllib2 import urlopen
from urlparse import urlparse
import sys
import tarfile
from tempfile import mkdtemp
import os
from imp import find_module, load_module
import distutils


class LinkListParser(HTMLParser):

    def __init__(self, package):
        HTMLParser.__init__(self)
        self.package = package
        self._href = None
        self._data = None
        self._links = {}

    @property
    def links(self):
        return self._links

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("rel") == "internal":
            self._href = a.get("href")
            self._data = ""

    def handle_data(self, data):
        if self._href:
            self._data += data

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            if self._data.startswith(self.package + "-") and self._data.endswith(".tar.gz"):
                name = self._data[len(self.package) + 1:-7]
                if self._href.startswith("../../"):
                    self._href = "https://pypi.python.org" + self._href[5:]
                self._links[name] = self._href
            self._href = None
            self._data = None


def get_versions(package):
    url = "https://pypi.python.org/simple/{0}/".format(package)
    f = urlopen(url)
    src = f.read()
    f.close()
    html = LinkListParser(package)
    html.feed(src)
    html.close()
    return html.links


#def install(package, version=None):
#    # download
#    versions = get_versions(package)
#    if version:
#        url = versions.get(version)
#    else:
#        url = versions[max(versions)]
#    if not url:
#        raise LookupError("Version not found")
#    parsed = urlparse(url)
#    f = parsed.path.split("/")[-1]
#    urlretrieve(url, f)
#    # unzip
#    tf = tarfile.open(f, "r:gz")
#    tf.extractall()
#    tf.close()
#    # setup


class Local(object):

    def __init__(self):
        pass

    def installed(module):
        try:
            x = find_module(module)
            m = load_module(module, *x)
        except ImportError:
            return None
        try:
            return m.__version__
        except AttributeError:
            return True


class Remote(object):

    def __init__(self):
        self._url = "https://pypi.python.org/"
        self._links = {}

    def get_versions(self, package):
        url = "https://pypi.python.org/simple/{0}/".format(package)
        f = urlopen(url)
        src = f.read()
        f.close()
        html = LinkListParser(package)
        html.feed(src)
        html.close()
        self._links[package] = html.links

    def download(self, package, version):
        if package not in self._links or version not in self._links[package]:
            self.get_versions(package)
        try:
            url = self._links[package][version]
        except KeyError:
            raise LookupError("Package not found")
        parsed = urlparse(url)
        f = parsed.path.split("/")[-1]
        urlretrieve(url, f)
        return f

    def install(self, package, version):
        f = self.download(package, version)
        tf = tarfile.open(f, "r:gz")
        tf.extractall()
        tf.close()
        # setup
        os.chdir(package + "-" + version)
        sys.argv[1:] = ["install"]
        execfile("setup.py")
        os.chdir("..")


def install(package, version):
    r = Remote()
    r.install(package, version)


def setup(*args, **kwargs):
    distutils.core.setup(*args, **kwargs)


if __name__ == "__main__":
    package = sys.argv[1]
    version = sys.argv[2]
    install(package, version)

