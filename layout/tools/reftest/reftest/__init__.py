# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import os
import re

RE_COMMENT = re.compile(r'\s+#')
RE_HTTP = re.compile(r'HTTP\((\.\.(\/\.\.)*)\)')
RE_PROTOCOL = re.compile(r'^\w+:')
FAILURE_TYPES = (
    'fails',
    'fails-if',
    'needs-focus',
    'random',
    'random-if',
    'silentfail',
    'silentfail-if',
    'skip',
    'skip-if',
    'slow',
    'slow-if',
    'fuzzy',
    'fuzzy-if',
    'require-or',
    'asserts',
    'asserts-if',
)
PREF_ITEMS = (
    'pref',
    'test-pref',
    'ref-pref',
)

class ReftestManifest(object):
    """Represents a parsed reftest manifest.

    We currently only capture file information because that is the only thing
    tools require.
    """
    def __init__(self):
        self.path = None
        self.dirs = set()
        self.files = set()
        self.manifests = set()

    def load(self, path):
        """Parse a reftest manifest file."""
        normalized = os.path.normpath(os.path.abspath(path))
        self.manifests.add(normalized)
        if not self.path:
            self.path = normalized

        mdir = os.path.dirname(normalized)
        self.dirs.add(mdir)

        with open(path, 'r') as fh:
            urlprefix = ''
            for line in fh:
                line = line.decode('utf-8')

                # Entire line is a comment.
                if line.startswith('#'):
                    continue

                # Comments can begin mid line. Strip them.
                m = RE_COMMENT.search(line)
                if m:
                    line = line[:m.start()]

                line = line.strip()
                if not line:
                    continue

                items = line.split()
                tests = []

                for i in range(len(items)):
                    item = items[i]

                    if item.startswith(FAILURE_TYPES):
                        continue
                    if item.startswith(PREF_ITEMS):
                        continue
                    if item == 'HTTP':
                        continue

                    m = RE_HTTP.match(item)
                    if m:
                        # Need to package the referenced directory.
                        self.dirs.add(os.path.normpath(os.path.join(
                            mdir, m.group(1))))
                        continue

                    if item == 'url-prefix':
                        urlprefix = items[i+1]
                        break

                    if item == 'default-preferences':
                        break

                    if item == 'include':
                        self.load(os.path.join(mdir, items[i+1]))
                        break

                    if item == 'load' or item == 'script':
                        tests.append(items[i+1])
                        break

                    if item == '==' or item == '!=':
                        tests.extend(items[i+1:i+3])
                        break

                for f in tests:
                    # We can't package about: or data: URIs.
                    # Discarding data isn't correct for a parser. But retaining
                    # all data isn't currently a requirement.
                    if RE_PROTOCOL.match(f):
                        continue

                    test = os.path.normpath(os.path.join(mdir, urlprefix + f))
                    self.files.add(test)
                    self.dirs.add(os.path.dirname(test))
