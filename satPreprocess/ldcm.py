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
import sys, numpy, os, time, glob
from osgeo           import gdal
from osgeo.gdalconst import *
from computeToa import ComputeToa


# Class Landsat 8 (LDCM)
class Landsat8(ComputeToa):
    """ Parsing of LDCM metadata"""

    def __init__(self, metafile):
        """Metadata for conversion to TOA Radiance and TOA Reflectance"""
        print 'metadata filename: %s' %(metafile)
        startTime = time.time()
        meta = open(metafile, 'r')
        metalines = meta.readlines()
        self.root = {}
        for line in metalines:
            if any(i in line for i in ('REFLECTANCE_MULT_BAND_','REFLECTANCE_ADD_BAND_',
                                       'K1_CONSTANT_BAND_','K2_CONSTANT_BAND_',
                                       'SUN_AZIMUTH','SUN_ELEVATION')):
                self.root[line.split('=')[0].strip()] = float(line.split('=')[1].strip())
        metalines = None
        meta.close()
        endTime = time.time()
        print'parsing duration: %s seconds' %(endTime-startTime)

    def getGain(self):
        """
        List of Landsat band-specific multiplicative rescaling factor and
        Band-specific additive rescaling factor
        (coastal/aerosol, blue, green, red, nir, swir1, swir2, pan, cirrus)
        """        
        self.gain = [self.root['REFLECTANCE_MULT_BAND_%s' %(i+1)] for i in range(9)]
        self.add = [self.root['REFLECTANCE_ADD_BAND_%s' %(i+1)] for i in range(9)]
    
    def getSolarAngle(self):
        """Solar Zenithal and Azimuthal Angles in degrees"""
        self.solarZAngle = 90 - self.root['SUN_ELEVATION']
        self.solarAAngle = self.root['SUN_AZIMUTH']

    def getBandList(self, dirname):
        """Gets list of spectral bands"""
        self.bandList = glob.glob(os.path.join(dirname,'LC*B[1-9].TIF'))

    def getDate(self):
        """Acquisition date"""
        self.Date = 'not required'
        
    def getDistEarthSun(self):
        """Not required"""
        self.distEarthSun = 'not required'

    def getSolarIrrad(self):
        """Not required"""
        self.eSun = ['not required']

    def reflectanceToa(self):
        """
        TOA Reflectance
        Equation for Landsat 8:
        r = (M*CN+A)/cos(thZ)
        with r for TOA reflectance
             M for band-specific multiplicative rescaling factor
             CN for pixel value (digital number)
             A for Band-specific additive rescaling factor
             thZ for Solar Zenithal angle
        """
        toa = (self.maxi*(self.gain[self.band]*self.data + self.add[self.band])/
               (numpy.cos(numpy.radians(self.solarZAngle)))).astype(self.nptype)
        return toa
