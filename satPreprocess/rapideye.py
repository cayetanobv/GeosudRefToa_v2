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
from osgeo import gdal
from osgeo.gdalconst import *
import xml.etree.ElementTree as ET
from distEarthSun import DistEarthSun
from computeToa import ComputeToa

# Class RapidEye
class RapidEye(DistEarthSun, ComputeToa):

    def __init__(self, metafile):
        """Metadata parsing (xml)"""
        print 'metadata filename: %s' %(metafile)
        startTime = time.time()
        tree = ET.parse(metafile)
        self.root = tree.getroot()
        self.ns = self.root.tag.split('{')[1].split('}')[0]
        tree = None
        endTime = time.time()
        print'parsing duration: %s seconds' %(endTime-startTime)

    def getGain(self):
        """
        List of RapidEye gain values (blue, green, red, rededge, nir)
        Metadata file root required
        """
        radioFactor = {}
        for elem in self.root.iter('{%s}bandSpecificMetadata' %(self.ns)):
            bandIndex = elem.find('{%s}bandNumber' %(self.ns)).text
            bandRadio = elem.find('{%s}radiometricScaleFactor' %(self.ns)).text
            radioFactor[bandIndex] = float(bandRadio)
        self.gain = [radioFactor[str(i+1)] for i in range(len(radioFactor))]

    def getSolarAngle(self):
        """Solar Zenithal and Azimuthal Angles in degrees"""
        for elem in self.root.iter('{%s}Acquisition' %(self.ns)):
            for i in elem:
                if 'illuminationElevationAngle' in i.tag:
                    self.solarZAngle = 90 - float(i.text)
                if 'illuminationAzimuthAngle' in i.tag:
                    self.solarAAngle = float(i.text)

    def getDate(self):
        """Acquisition date"""
        for elem in self.root.iter('{%s}Acquisition' %(self.ns)):
            for i in elem:
                if 'acquisitionDateTime' in i.tag:
                    self.date = i.text.split('T')[0].split('-')    

    def getSolarIrrad(self):
        """Solar irradiance values for each spectral band"""
        # solar irradiance : blue, green, red, rededge, nir
        self.eSun = [1997.8, 1863.5, 1560.4, 1395.0, 1124.4] 
        
    def reflectanceToa(self):
        """
        TOA Reflectance
        Equation for RapidEye:
        r = pi*dist^2*CN/(eSun*cos(thZ)*G)
        with r for TOA Reflectance
             dist for Earth-Sun Distance (in UA)
             CN for pixel value (digital number)
             eSun for Solar Irradiance
             thZ for Solar Zenithal angle
             G for gain
        """
        toa  = (self.maxi*(numpy.pi * self.distEarthSun**2 * self.data * self.gain[self.band])/
                (self.eSun[self.band]* numpy.cos(numpy.radians(self.solarZAngle)))).astype(self.nptype)
        return toa
