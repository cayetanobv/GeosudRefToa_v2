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

import os
from osgeo           import gdal
from osgeo.gdalconst import *
import numpy

class ComputeToa:
    """Loop for computing Toa"""

    def dnToToa(self, imgfile, outname='_refToa.tif', bitcode='32', outpath=None, nbBand='None'):
        """
        TOA Reflectance
        """
        # image driver
        driver = gdal.GetDriverByName('GTiff')
        driver.Register()
        # image opening
        inDs = gdal.Open(imgfile, GA_ReadOnly)
        if inDs is None:
            print 'could not open ' + imgfile
            sys.exit(1)
        # image size and tiles 
        cols  = inDs.RasterXSize
        rows  = inDs.RasterYSize
        bands = inDs.RasterCount
        xBSize = 60
        yBSize = 60
        procTot = cols*rows*bands
        procPar = 0

        # output image name
        if bitcode == '32':
            codage = GDT_Float32
            self.nptype = numpy.float
            self.maxi = 1
        elif bitcode == '16':
            codage = GDT_UInt16
            self.nptype = numpy.uint16
            self.maxi = 1000

        if outpath:
            outDs = driver.Create('%s%s' %(os.path.join(outpath,os.path.splitext(os.path.basename(imgfile))[0]),outname),
                                  cols, rows, bands, codage)
        else:
            outDs = driver.Create('%s%s' %(os.path.splitext(imgfile)[0], outname), cols, rows, bands, codage)
        if outDs is None:
            print 'could not create %s%s' %(os.path.splitext(imgfile)[0], outname)
            sys.exit(1)

        for band in range(bands):
            
            if nbBand != 'None':
                self.band = int(nbBand)
            else:
                self.band = band
            outBand = outDs.GetRasterBand(band + 1)
            canal   = inDs.GetRasterBand(band + 1)
            # line search
            for i in range(0, rows, yBSize):
                if i + yBSize < rows:
                    numRows = yBSize
                else:
                    numRows = rows - i
                # column search
                for j in range(0, cols, xBSize):
                    if j + xBSize < cols:
                        numCols = xBSize
                    else:
                        numCols = cols - j
                    self.data = canal.ReadAsArray(j,i,numCols, numRows).astype(numpy.float)
                    # TOA reflectance equation
                    toa  = self.reflectanceToa()
                    # saturated pixels (> 1 or > 1000)
                    mask = numpy.less_equal(toa, self.maxi)
                    toa  = numpy.choose(mask, (self.maxi, toa))
                    outBand.WriteArray(toa,j,i)
                    procPar += numRows*numCols
                    emit = (float(procPar)/procTot*100)
                    yield int(emit-1)
            outBand.FlushCache()
            stats = outBand.GetStatistics(0, 1)
            
            outBand = None
            canal = None
        # Import of inDs' GCPs
        outDs.SetGeoTransform(inDs.GetGeoTransform())
        outDs.SetProjection(inDs.GetProjection())
        outDs.SetGCPs(inDs.GetGCPs(),inDs.GetGCPProjection())
        # Metadata change in order to spedify a "point" origine for GCPs
        #(otherwise shift of 1/2 pixel)
        outDs.SetMetadataItem("AREA_OR_POINT", "Point")
        # pyramid layers processing
        gdal.SetConfigOption('USE_RRD', 'YES')
        outDs.BuildOverviews(overviewlist = [2,4,8,16,32,64,128])
        yield 100
        
        inDs  = None
        outDs = None

        
    

