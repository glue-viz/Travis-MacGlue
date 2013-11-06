#!/bin/sh -e

#binary installation of Qt
curl -OL http://download.qt-project.org/official_releases/qt/4.8/4.8.5/qt-mac-opensource-4.8.5.dmg
hdiutil attach qt-mac-opensource-4.8.5.dmg
sudo installer -pkg /Volumes/Qt\ 4.8.5/Qt.mpkg -target /
