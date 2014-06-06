#!/bin/sh -e

#binary installation of Qt
curl -OL http://download.qt-project.org/official_releases/qt/4.8/4.8.6/qt-opensource-mac-4.8.6-1.dmg
hdiutil attach qt-opensource-mac-4.8.6-1.dmg
sudo installer -pkg /Volumes/Qt\ 4.8.6/Qt.mpkg -target /
