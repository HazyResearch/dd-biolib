#!/bin/sh
set -eu
PARSER="stanford-corenlp-full-2015-12-09"
rm -fr bin
url=http://nlp.stanford.edu/software/${PARSER}.zip
if type curl &>/dev/null; then
    curl -RLO $url
elif type wget &>/dev/null; then
    wget -N -nc $url
fi
unzip ${PARSER}.zip
mv ${PARSER} bin
rm ${PARSER}.zip
printf '# Ignore everything in this directory\n*\n# Except this file\n!.gitignore' > bin/.gitignore




