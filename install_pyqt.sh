#!/bin/sh -e

#binary installation of Qt
curl -OL http://download.qt-project.org/official_releases/qt/4.8/4.8.4/qt-mac-opensource-4.8.4.dmg
hdiutil attach qt-mac-opensource-4.8.4.dmg
sudo installer -pkg /Volumes/Qt\ 4.8.4/Qt.mpkg -target /

#binary installation of PyQt
#curl -OL http://sourceforge.net/projects/pyqtx/files/Complete/PyQtX%2B_py273_q482_pyqt494.pkg.mpkg.zip/download
#unzip PyQtX\+_py273_q482_pyqt494.pkg.mpkg.zip
#sudo installer -pkg PyQtX\+_py273_q482_pyqt494.pkg.mpkg -target /

#sip
curl -OL http://sourceforge.net/projects/pyqt/files/sip/sip-4.14.6/sip-4.14.6.tar.gz
tar -xvf sip-4.14.6.tar.gz
cd sip-4.14.6
#sip wants a Framework python, but seems unnecessary. Remove test
sed -i .bak s/if\ \"Python/if\ False\ and\ \"Python/g siputils.py
python configure.py
make
sudo make install

#PyQt
cd ..
curl -OL http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.10.1/PyQt-x11-gpl-4.10.1.tar.gz
tar -xvf PyQt-x11-gpl-4.10.1.tar.gz
cd PyQt-x11-gpl-4.10.1
python configure.py --confirm-license -q /usr/bin/qmake --concatenate -e QtCore -e QtGui -e QtTest -e QtXml -e QtSvg
make
sudo make install

#pyuic4 references pythonw2.7, which Anaconda calls python2.7
sed -i bak s/pythonw2.7/pythonw/ `which pyuic4`
