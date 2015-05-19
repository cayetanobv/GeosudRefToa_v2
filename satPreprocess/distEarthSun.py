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

import numpy

class DistEarthSun:
    """Gets the distance between earth and sun according
    to the acquisition date"""
    
    def getDistEarthSun(self):
        """
        Earth-Sun Distance (UA)
        Equation used (in degrees) :
        | 1-e*cos(r*(JD-4))                              |
        | where  e : Orbital eccentricity (0.01674)      |
        |        r : Mean rotation angle (0.9856 deg/day)|
        |       JD : Julian-day                          |
        """
        # Creation of julian-day table for leap year
        table_bi = {}
        anbi_nbj = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        i = 1
        for mois in range(len(anbi_nbj)):
            for jour in range(1,anbi_nbj[mois]+1):
                table_bi[mois+1, jour] = i
                i += 1

        # Creation of julian-day table for non-leap year
        table_no = {}
        anno_nbj = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        i = 1
        for mois in range(len(anno_nbj)):
            for jour in range(1,anno_nbj[mois]+1):
                table_no[mois+1, jour] = i
                i += 1

        # Earth-Sun distance calculation
        if int(self.date[0])%400==0 or (int(self.date[0])%4 == 0 and int(self.date[0])%100!=0):
            print "leap year"
            jour = table_bi[int(self.date[1]),int(self.date[2])]
            print "the input day is " + str(jour) + "th of the year " + self.date[0]
            distance_form = 1-0.01674*numpy.cos((numpy.pi/180)*0.9856*(jour-4))
            print "the Earth-Sun distance (in UA) is: %s" %(distance_form)
        else:
            print "non-leap year"
            jour = table_no[int(self.date[1]),int(self.date[2])]
            print "the input day is " + str(jour) + "th of the year " + self.date[0]
            distance_form = 1-0.01674*numpy.cos((numpy.pi/180)*0.9856*(jour-4))
            print "the Earth-Sun distance (in UA) is: %s" %(distance_form)

        self.distEarthSun = distance_form        
