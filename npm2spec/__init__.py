#-*- coding: utf-8 -*-

"""
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 (C) 2012 - Pierre-Yves Chibon <pingou@pingoured.fr>
 (C) 2014 - Ralph Bean <rbean@redhat.com>
"""

import argparse
import ConfigParser
import logging
import shutil
import tarfile
import os
import urllib2

from subprocess import Popen, PIPE
from tarfile import TarError

logging.basicConfig()
LOG = logging.getLogger('NPM2spec')
#LOG.setLevel('DEBUG')
__version__ = '0.3.0'

ALREADY_PACKAGED = [
    'coffee-script',
]


def create_conf(configfile):
    """Check if the provided configuration file exists, generate the
    folder if it does not and return True or False according to the
    initial check.

    :arg configfile, name of the configuration file looked for.
    """
    if not os.path.exists(configfile):
        dirn = os.path.dirname(configfile)
        if not os.path.exists(dirn):
            os.makedirs(dirn)
        return True
    return False


def save_config(configfile, parser):
    """"Save the configuration into the specified file.

    :arg configfile, name of the file in which to write the configuration
    :arg parser, ConfigParser object containing the configuration to
    write down.
    """
    conf = open(configfile, 'w')
    parser.write(conf)
    conf.close()


def get_logger():
    """ Return the logger. """
    return LOG


def get_rpm_tag(tag):
    """" Reads the .rpmmacros and set the values accordingly
    Code from José Matos.
    :arg tag, the rpm tag to find the value of
    """
    dirname = Popen(["rpm", "-E", '%' + tag], stdout=PIPE).stdout.read()[:-1]
    return dirname


def move_sources(fullpath, sources):
    """ Copy the tarball from its current location to the sourcedir as
    defined by rpm.

    :arg fullpath, the fullpath to the sources in their current location.
    :arg sources, the name of the file in which the origin will be copied.
    """
    sourcedir = get_rpm_tag('_sourcedir')
    dest = '%s/%s' % (sourcedir, sources)
    shutil.copyfile(fullpath, dest)


def get_packager_name():
    """ Query rpm to retrieve a potential packager name from the
    .rpmmacros.
    """
    packager = get_rpm_tag('%packager')
    if not packager.startswith('%'):
        packager = packager.split('<')[0].strip()
        return packager
    else:
        return ''

def get_packager_email():
    """ Query rpm to retrieve a potential packager email from the
    .rpmmacros.
    """
    packager = get_rpm_tag('%packager')
    if not packager.startswith('%'):
        packager = packager.split('<', 1)[1].rsplit('>', 1)[0].strip()
        return packager
    else:
        return ''


class Settings(object):
    """ NPM2spec user config Setting"""
    # Editor to use in the spec
    packager = get_packager_name()
    # Editor email to use in the spec
    email = get_packager_email()

    def __init__(self):
        """Constructor of the Settings object.
        This instanciate the Settings object and load into the _dict
        attributes the default configuration which each available option.
        """
        self._dict = {
                        'packager': self.packager,
                        'email': self.email,
                    }
        self.load_config('.config/npm2spec', 'main')

    def load_config(self, configfile, sec):
        """Load the configuration in memory.

        :arg configfile, name of the configuration file loaded.
        :arg sec, section of the configuration retrieved.
        """
        parser = ConfigParser.ConfigParser()
        configfile = os.environ['HOME'] + "/" + configfile
        is_new = create_conf(configfile)
        parser.read(configfile)
        if not parser.has_section(sec):
            parser.add_section(sec)
        self.populate(parser, sec)
        if is_new:
            save_config(configfile, parser)

    def set(self, key, value):
        """ Set the value to the given key in the settings.

        :arg key, name of the parameter to set from the settings.
        :arg value, value of the parameter to set from the settings.
        """
        if not key in self._dict.keys():
            raise KeyError(key)
        self._dict[key] = value

    def get(self, key):
        """ Return the associated with the given key in the settings.

        :arg key, name of the parameter to retrieve from the settings.
        """
        if not key in self._dict.keys():
            raise KeyError(key)
        return self._dict[key]

    def populate(self, parser, section):
        """"Set option values from a INI file section.

        :arg parser: ConfigParser instance (or subclass)
        :arg section: INI file section to read use.
        """
        if parser.has_section(section):
            opts = set(parser.options(section))
        else:
            opts = set()

        for name in self._dict.iterkeys():
            value = None
            if name in opts:
                value = parser.get(section, name)
                parser.set(section, name, value)
                self._dict[name] = value
            else:
                parser.set(section, name, self._dict[name])


class NPM2specError(Exception):
    """ NPM2specError class
    Template for all the error of the project
    """

    def __init__(self, message):
        """ Constructor. """
        super(NPM2specError, self).__init__(message)
        self.message = message

    def __str__(self):
        """ Represent the error. """
        return str(self.message)


class NPM2spec(object):
    """ NPM2spec main class whose goal is to get the all the info
    needed for the spec file.
    """

    def __init__(self, name):
        """ Constructor.
        :arg name, the name of the library on the npm website.
        """
        self.name = name
        self.description = ''
        self.log = get_logger()
        self.version = ''
        self.summary = ''
        self.license = ''
        self.url = 'https://www.npmjs.org/package/%s' % name
        self.source0 = ''
        self.source = ''
        self.arch = False

    def download(self, force=False):
        """ Download the source of the package into the source directory
        which we retrieve from rpm directly.

        arg force, boolean whether to force the download of the sources
        even if they are on the system already.
        """
        sourcedir = get_rpm_tag('_sourcedir')
        sources = '%s/%s' % (sourcedir, self.source)

        if not force and os.path.exists(sources) and os.path.isfile(sources):
            self.log.info(
                "Sources are already present, no need to re-download")
            return

        url = self.source0.rsplit('/', 1)[0]
        url = '{url}/{source}'.format(url=url, source=self.source)
        print 'Downloading %s' % url

        try:
            remotefile = urllib2.urlopen(url)
        except urllib2.HTTPError, err:
            self.log.debug(err)
            raise NPM2specError('Could not retrieve source: %s' % url)
        localfile = open(sources, 'w')
        localfile.write(remotefile.read())
        localfile.close()

    def extract_sources(self):
        """ Extract the sources into the current directory. """
        sourcedir = get_rpm_tag('_sourcedir')
        tarball = "%s/%s" % (sourcedir, self.source)
        self.log.info("Opening: %s" % tarball)
        try:
            tar = tarfile.open(tarball)
            tar.extractall()
            tar.close()
        except (TarError, IOError), err:
            self.log.debug("Error while extracting the tarball")
            self.log.debug("ERROR: %s" % err)

    def get_doc_files(self):
        possible = set([
            'README', 'README.md', 'README.txt',
            'LICENSE', 'LICENSE-MIT',
            'CHANGELOG', 'CHANGELOG.md', 'CHANGELOG.txt',
            'HISTORY', 'HISTORY.md', 'HISTORY.txt',
            'NEWS', 'NEWS.md', 'NEWS.txt',
        ])
        try:
            actual = set(os.listdir('package'))
            return possible.intersection(actual)
        except Exception:
            return set(['COULDNT_DETECT_FILES'])

    def get_package_files(self):
        possible = set([
            'package.json',
            'lib',
            'tasks',
        ])
        try:
            actual = set(os.listdir('package'))
            definite = possible.intersection(actual)
            for item in actual:
                if item not in definite and item.endswith('.js'):
                    definite.add(item)
            return definite
        except Exception:
            return set(['COULDNT_DETECT_FILES'])

    def remove_sources(self):
        """ Remove the source we extracted in the current working
        directory.
        """
        source = 'package'
        self.log.info('Removing extracted sources: "%s"' % source)
        try:
            shutil.rmtree(source)
        except (IOError, OSError), err:
            self.log.info('Could not remove the extracted sources: "%s"'\
                % source)
            self.log.debug('ERROR: %s' % err)

    def retrieve_info(self):
        """ Retrieve all the information from npm to fill up the spec
        file.
        """
        import requests

        url = "http://registry.npmjs.org/%s" % self.name
        response = requests.get(url)
        data = response.json()

        if 'versions' not in data:
            raise ValueError("ridiculous")

        versions = [tuple(s.split('.')) for s in data['versions'].keys()]
        self.version = '.'.join(sorted(versions)[-1])
        self.source0 = data['versions'][self.version]['dist']['tarball']
        self.source = self.source0.rsplit('/')[-1]
        self.summary = data['description']
        self.description = data.get('readme', 'NO DESCRIPTION')
        self.license = data.get('license', "NO LICENSE")
        latest = data['versions'][self.version]

        self.deps = {}
        if 'dependencies' in latest:
            self.deps.update(latest['dependencies'])
        if 'peerDependencies' in latest:
            self.deps.update(latest['peerDependencies'])

        self.dev_deps = {}
        if 'devDependencies' in latest:
            self.dev_deps.update(latest['devDependencies'])

        self.test_command = None
        scripts = latest.get('scripts', {})
        if isinstance(scripts, dict):
            self.test_command = scripts.get('test')

class NPM2specUI(object):
    """ Class handling the user interface. """

    def __init__(self):
        """ Constructor.
        """
        self.parser = None
        self.log = get_logger()
        self.seen = set()

    def setup_parser(self):
        """ Command line parser. """
        self.parser = argparse.ArgumentParser(usage='%(prog)s [options]',
                prog='npm2spec')
        self.parser.add_argument('--version', action='version',
            version='%(prog)s ' + __version__)
        self.parser.add_argument('package',
            help='Name of the npm library to package.')
        self.parser.add_argument('--recurse', action='store_true',
            help='Recursively generate specs for unpackaged deps.')
        self.parser.add_argument('--enable-tests', action='store_true',
            help='Turn on tests in the test suite(s).')
        self.parser.add_argument('--verbose', action='store_true',
            help='Give more info about what is going on.')
        self.parser.add_argument('--debug', action='store_true',
            help='Output bunches of debugging info.')

    def main(self):
        """ Main function.
        Entry point of the program.
        """
        try:
            self.setup_parser()
            args = self.parser.parse_args()

            self.log = get_logger()
            if args.verbose:
                self.log.setLevel('INFO')
            if args.debug:
                self.log.setLevel('DEBUG')

            self.workon(args.package, args.recurse, args.enable_tests)
        except NPM2specError, err:
            print err

    def workon(self, package, recurse, enable_tests, parents=None):
        self.seen.add(package)

        parents = parents or []
        import pkgwat.api
        from spec import Spec

        def handle_deps(deps):
            for name, version in deps.items():
                if name in self.seen:
                    self.log.info('  *****  Already seen %r' % name)
                    continue
                self.seen.add(name)
                self.log.info("(%i) %s" % (
                    len(self.seen),
                    " -> ".join(parents + [name])
                ))

                try:
                    pkgwat.api.get('nodejs-' + name)
                    self.log.info('  nodejs-%s is already packaged' % name)
                    continue
                except KeyError:
                    pass

                specfile = os.path.expanduser(
                    '~/rpmbuild/SPECS/nodejs-%s' % name)
                if os.path.exists(specfile):
                    self.log.info('  local spec for nodejs-%s exists' % name)
                    continue

                if name in ALREADY_PACKAGED:
                    self.log.info('  %s packaged and in white list' % name)
                    continue

                self.workon(name, recurse, enable_tests, parents + [name])

        npm = NPM2spec(package)
        try:
            npm.retrieve_info()
        except ValueError:
            return

        if recurse:
            handle_deps(npm.deps)
            handle_deps(npm.dev_deps)

        npm.download()

        npm.extract_sources()
        doc_files = npm.get_doc_files()
        npm.doc_files = doc_files
        package_files = npm.get_package_files()
        npm.package_files = package_files
        npm.remove_sources()

        settings = Settings()
        spec = Spec(settings, npm, enable_tests=enable_tests)
        spec.fill_spec_info()
        spec.get_template()
        spec.write_spec()


def main():
    """ Entry point used in the setup.py.
    This just calls the main function in NPM2specUI.
    """
    return NPM2specUI().main()

if __name__ == '__main__':
    #import sys
    #sys.argv.append('npm2spec')
    main()
