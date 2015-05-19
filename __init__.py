# -*- coding: utf-8 -*-
"""
/***************************************************************************
 geosudRefToa
                                 A QGIS plugin
 TOA reflectance conversion for Geosud satellite data
                             -------------------
        begin                : 2015-04-22
        copyright            : (C) 2015 by Kenji Ose / Irstea
        email                : kenji.ose@teledetection.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load geosudRefToa class from file geosudRefToa.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geosud_ref_toa import geosudRefToa
    return geosudRefToa(iface)
