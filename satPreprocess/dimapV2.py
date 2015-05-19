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


# libraries
import sys, numpy, os, time
from osgeo           import gdal
from osgeo.gdalconst import *
import xml.etree.ElementTree as ET
from distEarthSun import DistEarthSun
from computeToa import ComputeToa

# Class Spot6/7
class DimapV2(DistEarthSun, ComputeToa):
    """ Parsing of Dimap v.2 metadata"""
        
    def __init__(self, metafile):
        """Metadata parsing (xml)"""
        print 'metadata filename: %s' %(metafile)
        startTime = time.time()
        tree = ET.parse(metafile)
        self.root = tree.getroot()
        tree = None
        endTime = time.time()
        print'parsing duration: %s seconds' %(endTime-startTime)
        
    def getGain(self):
        """
        List of Spot5 gain values (green, red, nir, mir)
        Metadata file root required
        """
        radioFactor = {}
        for elem in self.root.iter('Band_Radiance'):
            bandIndex = elem.find('BAND_ID').text
            bandRadio = elem.find('GAIN').text
            radioFactor[bandIndex[1]] = float(bandRadio)
        # reorder gains according to band order in the image file (r, g, b, nir)
        self.gain = [radioFactor['2'],radioFactor['1'],radioFactor['0'],radioFactor['3']]

    def getSolarAngle(self):
        """Solar Zenithal and Azimuthal Angles in degrees"""
        solarAAngleList = list()
        solarZAngleList = list()
        for elem in self.root.iter('Solar_Incidences'):
            print elem
            solarAAngleList.append(float(elem.find('SUN_AZIMUTH').text))
            solarZAngleList.append(90 - float(elem.find('SUN_ELEVATION').text))
        #average of solar azimuth and zenithal angles
        self.solarAAngle = numpy.mean(solarAAngleList)
        self.solarZAngle = numpy.mean(solarZAngleList)

    def getDate(self):
        """Acquisition date"""
        self.date = self.root.find(
            'Dataset_Sources/Source_Identification/Strip_Source/IMAGING_DATE').text.split('-')

    def getSolarIrrad(self):
        """Solar irradiance values for each spectral band"""
        solarIrrad = {}
        for elem in self.root.iter('Band_Solar_Irradiance'):
            bandIndex = elem.find('BAND_ID').text
            bandRadio = elem.find('VALUE').text
            solarIrrad[bandIndex[1]] = float(bandRadio)
        # reorder solar irradiance according to band order in the image file (r, g, b, nir)
        self.eSun = [solarIrrad['2'],solarIrrad['1'],solarIrrad['0'],solarIrrad['3']]      

    def reflectanceToa(self):
        """
        TOA Reflectance
        Equation for Spot6/7 and Pleaides:
        r = pi*dist^2*CN/(eSun*cos(thZ)*G)
        with r for TOA Reflectance
             dist for Earth-Sun Distance (in UA)
             CN for pixel value (digital number)
             eSun for Solar Irradiance
             thZ for Solar Zenithal angle
             G for gain
        """
        toa  = (self.maxi*(numpy.pi * self.distEarthSun**2 * self.data)/
                (self.gain[self.band] * self.eSun[self.band] * numpy.cos(numpy.radians(self.solarZAngle)))).astype(self.nptype)
        return toa
