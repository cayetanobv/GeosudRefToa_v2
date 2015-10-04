# -*- coding: utf-8 -*-
"""
/***************************************************************************
 geosudRefToa
                                 A QGIS plugin
 TOA reflectance conversion for Geosud satellite data
                              -------------------
        begin                : 2015-04-22
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Kenji Ose / Irstea
        email                : kenji.ose@teledetection.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QSizePolicy, QFileDialog, QWidget, QProgressBar, QLabel
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from geosud_ref_toa_dialog import geosudRefToaDialog
import os.path
#KO_Import
from qgis.gui import *
from qgis.utils import showPluginHelp
from satPreprocess import rapideye, spot, ldcm, dimapV2
import xml.etree.ElementTree as ET
import time


class geosudRefToa():
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'geosudRefToa_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = geosudRefToaDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geosud Toa Reflectance')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'geosudRefToa')
        self.toolbar.setObjectName(u'geosudRefToa')

        #KO_QGis Info Bar
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.dlg.glInfo.addWidget(self.bar, 0,0,1,1)

        #KO_Connect
        self.dlg.pbLoadImg.clicked.connect(self.displayDirFile)
        self.dlg.pbMetadata.clicked.connect(self.displayDirMetadata)
        self.dlg.pbLucky.clicked.connect(self.autoLoadMetadata)
        self.dlg.pbGetParam.clicked.connect(self.displayMetadata)
        self.dlg.cbOutput.clicked.connect(self.activeOutputDir)
        self.dlg.pbOutput.clicked.connect(self.outputDir)
        self.dlg.pbConvert.clicked.connect(self.processToa)
        self.dlg.pbAbout.clicked.connect(self.helpFile)
        self.dlg.pbClear.clicked.connect(self.clearHistory)

        #KO_Disabled
        self.dlg.pbOutput.setEnabled(False)
        self.dlg.cbOutput.setEnabled(False)
        self.dlg.pbConvert.setEnabled(False)
        self.dlg.leOutput.setEnabled(False)

        #KO_Checked
        self.dlg.rbRefNorm.setChecked(True)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('geosudRefToa', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/geosudRefToa/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'convert DN to reflectance'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&Geosud Toa Reflectance'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #KO_Load Image Files
    def displayDirFile(self):
        """Displays input image file"""
        imgList = QFileDialog.getOpenFileNames(self.dlg,
                                               u'Satellite Image or Bands',
                                               self.lastUsedPath('imgPath'),
                                               "Image files (*.tif)")
        if imgList != []:
            self.setLastUsedPath('imgPath',os.path.dirname(imgList[0]))
        self.dlg.leInput.setText(','.join(imgList))
        self.clearFields()
        self.unCheck()
        self.metafile = None

    #KO_Load Metadata Files
    def displayDirMetadata(self):
        """Displays input metadata file"""
        metadata = QFileDialog.getOpenFileName(self.dlg,
                                               u'Image Metadata',
                                               self.lastUsedPath('mdPath'),
                                               u"Spot/Pléiades (*.dim *.xml);;RapidEye (*.xml);;Landsat (*.txt)")
        if metadata != '':
            self.setLastUsedPath('mdPath', os.path.dirname(metadata))
        self.dlg.leMetadata.setText(metadata)

    #KO_AutoLoad Metadata Files
    def autoLoadMetadata(self):
        """Tries to load automatically the metadata file and the instrument type"""
        imgPath = os.path.dirname(self.dlg.leInput.text().split(',')[0])
        listExtension = ['.dim','.xml','.txt']
        listFiles = list()
        self.instrument = -1
        try:
            for dirname, dirnames, filenames in os.walk(imgPath):
                for filename in filenames:
                    if os.path.splitext(filename)[1].lower() in listExtension and \
                    '.aux' not in os.path.splitext(filename)[0].lower():
                            listFiles.append(filename)
            for mdFile in listFiles:
                if 'dim' in mdFile.lower():
                    if mdFile.lower() == u'metadata.dim':
                        self.instrument = 2
                    elif 'phr' in mdFile.lower():
                        self.instrument = 4
                    elif any(i in mdFile.lower() for i in ['spot6', 'spot7']):
                        self.instrument = 3
                elif all(i in mdFile.lower() for i in ['metadata', 're']):
                    self.instrument = 1
                elif 'mtl.txt' in mdFile.lower():
                    self.instrument = 0
            metafile = os.path.join(imgPath, mdFile)
            if self.instrument != -1 and os.path.exists(metafile):
                self.dlg.leMetadata.setText(metafile)
                self.setLastUsedPath('mdPath',os.path.dirname(metafile))
                self.dlg.comboBox.setCurrentIndex(self.instrument)
        except(UnboundLocalError):
            self.bar.pushMessage("Info", "Image file required",
                                 level=QgsMessageBar.WARNING, duration=3)
            self.dlg.leMetadata.clear()

    #KO_Display Metadata
    def displayMetadata(self):
        """Shows required parameters from the metadata"""
        self.dlg.teParam.clear()
        self.imgfile = self.dlg.leInput.text().split(',')
        self.metafile = self.dlg.leMetadata.text()
        bandIndex = {0:'<b>band index:</b><br> 1: coastal/aerosol<br>\
                                               2: blue<br>\
                                               3: green<br>\
                                               4: red<br>\
                                               5: nir<br>\
                                               6: swir1<br>\
                                               7: swir2<br>\
                                               8: pan<br>\
                                               9: cirrus<br>',
                     1:'<b>band index:</b><br> 1: blue<br>\
                                               2: green<br>\
                                               3: red<br>\
                                               4: rededge<br>\
                                               5: nir<br>',
                     2:'<b>band index:</b><br> 1: nir<br>\
                                               2: red<br>\
                                               3: green<br>\
                                               4: swir<br>',
                     3:'<b>band index:</b><br> 1:red<br>\
                                               2:green<br>\
                                               3:blue<br>\
                                               4:nir<br>',
                     4:'<b>band index:</b><br> 1:red<br>\
                                               2:green<br>\
                                               3:blue<br>\
                                               4:nir<br>'}

        try:
            instrument = self.dlg.comboBox.currentText()
            instrumentId = self.dlg.comboBox.currentIndex()
            self.dlg.teParam.append('<b>instrument:</b><br>%s<br>' %(instrument))
            self.dlg.teParam.append('<b>image:</b>')
            self.dlg.teParam.append((''.join(['%s<br>']*len(self.imgfile)))
                                    %tuple([os.path.basename(i) for i in self.imgfile]))
            self.dlg.teParam.append('<b>metadata:</b><br>%s<br>'
                                    %(os.path.basename(self.metafile)))
            self.dlg.teParam.append(bandIndex[instrumentId])

            self.importMetadata(instrumentId)

            self.dlg.teParam.append('<b>gain:</b>')
            self.dlg.teParam.append((''.join(['%s<br>']*len(self.meta.gain)))
                                    %tuple(self.meta.gain))
            if hasattr(self.meta,'add'):
                self.dlg.teParam.append('<b>offset:</b>')
                self.dlg.teParam.append((''.join(['%s<br>']*len(self.meta.add)))
                                        %tuple(self.meta.add))
            self.dlg.teParam.append('<b>solar zenithal angle:</b><br> %s<br>'
                                    %(self.meta.solarZAngle))
            self.dlg.teParam.append('<b>Earth-Sun distance:</b><br> %s<br>'
                                    %(self.meta.distEarthSun))
            self.dlg.teParam.append('<b>solar irradiance:</b>')
            self.dlg.teParam.append((''.join(['%s<br>']*len(self.meta.eSun)))
                                    %tuple(self.meta.eSun))
            self.activeProcess()
        except (ET.ParseError, KeyError, IndexError):
            self.bar.pushMessage("Info", "Verify the instrument type",
                                 level=QgsMessageBar.WARNING, duration=3)
        except (IOError, AttributeError, TypeError):
            self.dlg.teParam.clear()
            self.bar.pushMessage("Info", "Metadata file or Image file required",
                                 level=QgsMessageBar.WARNING, duration=3)


    #KO_Import Metadata
    def importMetadata(self, instrumentId):
        """Imports required parameters from the metadata"""
        if instrumentId == 0:
            self.meta = ldcm.Landsat8(self.metafile)
        elif instrumentId == 1:
            self.meta = rapideye.RapidEye(self.metafile)
        elif instrumentId == 2:
            self.meta = spot.Spot5(self.metafile)
        elif instrumentId >= 3:
            self.meta = dimapV2.DimapV2(self.metafile)

        self.meta.getGain()
        self.meta.getSolarAngle()
        self.meta.getDate()
        self.meta.getDistEarthSun()
        self.meta.getSolarIrrad()

    #KO_Processing TOA reflectance
    def processToa(self):
        """Converts DN to TOA reflectance"""
        startTime = time.time()
        if self.dlg.cbOutput.isChecked() and os.path.exists(self.dlg.leOutput.text()):
            outputPath = self.dlg.leOutput.text()
        else:
            outputPath = os.path.dirname(self.dlg.leInput.text().split(',')[0])
        if self.dlg.rbRefNorm.isChecked():
            bitcode = '32'
            outname = '_refToa32.tif'
        elif self.dlg.rbRefMilli.isChecked():
            bitcode = '16'
            outname = '_refToa16.tif'

        progressMessageBar = self.iface.messageBar().createMessage("DN to TOA conversion...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progress.setTextVisible(False)
        label = QLabel()
        label.setText('  {0}%'.format(0))
        progressMessageBar.layout().addWidget(label)
        progressMessageBar.layout().addWidget(progress)

        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)

        if self.dlg.comboBox.currentIndex() == 0:
            bandList = self.dlg.leInput.text().split(',')
            idBand = {int(os.path.splitext(os.path.basename(i))[0][-1])-1:i for i in bandList}
            for band in idBand.keys():
                self.imgfile = idBand[band]
                nbBand = band
                self.history(outputPath, outname)
                for i in self.meta.dnToToa(self.imgfile, outname=outname, bitcode=bitcode, outpath=outputPath, nbBand=nbBand):
                    progress.setValue(i)
                    label.setText('{0}%'.format(i))
        else:
            self.imgfile = self.dlg.leInput.text().split(',')[0]
            self.history(outputPath, outname)
            for i in self.meta.dnToToa(self.imgfile, outname=outname, bitcode=bitcode, outpath=outputPath):
                progress.setValue(i)
                label.setText('{0}%'.format(i))
        self.iface.messageBar().clearWidgets()
        self.bar.pushMessage("Image processed !", level=QgsMessageBar.INFO, duration=3)
        endTime = time.time()

        self.dlg.teHistory.append('<b>reflectance processing duration:</b><br>{0} seconds<br>'.format(str(endTime - startTime)))

    #KO_Last used path
    def lastUsedPath(self, key):
        """Saves the last used path"""
        imgPath = self.dlg.leInput.text().split(',')[0]
        mdPath = self.dlg.leMetadata.text()
        path = '.'
        if key == 'imgPath':
            if os.path.exists(imgPath):
                path = os.path.dirname(imgPath)
        if key == 'mdPath':
            if not os.path.exists(mdPath):
                path = os.path.dirname(imgPath)
        return QSettings().value(key, path)

    #KO_Set last used path
    def setLastUsedPath(self, key, value):
        """Sets the used path"""
        QSettings().setValue(key, value)

    #KO_Active processes
    def activeProcess(self):
        """Activates processing buttons"""
        self.dlg.cbOutput.setEnabled(True)
        self.dlg.pbConvert.setEnabled(True)
        self.dlg.leOutput.setEnabled(True)

    #KO_Clear fields
    def clearFields(self):
        """Clears fields"""
        self.dlg.leMetadata.clear()
        self.dlg.teParam.clear()
        self.dlg.leOutput.clear()

    #KO_Uncheck
    def unCheck(self):
        """Unchecks processing buttons"""
        self.dlg.pbOutput.setEnabled(False)
        self.dlg.cbOutput.setChecked(False)
        self.dlg.cbOutput.setEnabled(False)
        self.dlg.pbConvert.setEnabled(False)
        self.dlg.leOutput.setEnabled(False)

    #KO_Active output Directory
    def activeOutputDir(self):
        """Activates output buttons"""
        if self.dlg.cbOutput.isChecked():
            self.dlg.pbOutput.setEnabled(True)
            self.dlg.leOutput.setEnabled(True)
        else:
            self.dlg.pbOutput.setEnabled(False)
            self.dlg.leOutput.setEnabled(False)

    #KO_Output Directory
    def outputDir(self):
        """Sets output directory"""
        outputFile = QFileDialog.getExistingDirectory(self.dlg,
                                                      u'Output directory',
                                                      self.lastUsedPath('outPath'))
        if outputFile != '':
            self.setLastUsedPath('outPath', outputFile)
        self.dlg.leOutput.setText(outputFile)

    #KO_Help file
    def helpFile(self):
        """Shows html About page"""
        showPluginHelp()

    #KO_History
        """History log"""
    def history(self,outputPath, outname):
        self.dlg.teHistory.append('---<br>')
        self.dlg.teHistory.append('<b>input image file:</b><br>{0}/<b>{1}</b><br>'.format(os.path.dirname(self.imgfile),
                                                                                   os.path.basename(self.imgfile)))
        self.dlg.teHistory.append('<b>output image file:</b><br>{0}/<b>{1}{2}</b><br>'.format(outputPath,
                                                                                       os.path.splitext(os.path.basename(self.imgfile))[0],
                                                                                       outname))

    def clearHistory(self):
        """Clears History text"""
        self.dlg.teHistory.clear()

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            #pass
        if result == 0:
            self.dlg.leInput.clear()
            self.clearFields()
            self.unCheck()
