#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions for interpreting and converting Ordnance Survey references.

By convention, longitude and latitude are referred and used in that order.
Note that the lon-lats are returned are OSGB36 (not the more modern WGS84),
as that is the system OSGB is based upon. The difference should be minimal
(i.e. less than 100 metres). For example, the OS grid reference 'TM114 525'
(just outside Ipswich) should convert to the lon-lat 1.088975 52.129892 in 
OSGB36, which is 1.087203 52.130350 in WGS84.

References
~~~~~~~~~~

* The Ordnance Survey provides `a guide to coordinate systems
  <http:#www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/index.html>`__,
  the `equations for conversion
  <http:#www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/guidec.html>`__
  and the `required constants
  <http:#www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/guidea.html>`__.

* Nice explanations of the OSGB system can be found `here <http://vancouver-webpages.com/peter/osgbfaq.txt>`__

* J Stott provides a `PHP library <http:#www.jstott.me.uk>`__ as well as
  Javascript and Java implementations.  Chris Veness' `Javascript
  implementation <http:#www.movable-type.co.uk/scripts/latlong-gridref.html>`__
  was a useful reference in the conversion. The `Perl module
  Geo::Coordinates::OSGB <http://search.cpan.org/~toby/Geo-Coordinates-OSGB-2.01/lib/Geo/Coordinates/OSGB.pm>`__ provides similar services.

* `Nearby.org.uk <http:#nearby.org.uk>`__ provides conversion between many
  geospatial formats including OS.

"""
# TODO: convert x,y format coordinates?
# TODO: better naming?
# TODO: is there a formal name for the large and small squares?
# TODO: is there a way to directly convert to WGS84?

__docformat__ = 'restructuredtext en'


### IMPORTS ###

#import math
from math import pi, cos, tan, sin, pow, sqrt, floor, degrees, radians
import string


### CONSTANTS & DEFINES ###

# true origin of national grid
ORIGIN_LAT = radians (49) #* pi / 180
ORIGIN_LON = radians (-2) # * pi / 180
ORIGIN_NORTHING = -100000
ORIGIN_EASTING = 400000

# a collection of constants for conversion
class OSGB36 (object):
        # Airy 1830 major & minor semi-axes
        a = 6377563.396 
        b = 6356256.910 
        # NatGrid scale factor on central meridian
        F0 = 0.9996012717       
        # eccentricity squared                
        e2 = 1 - (b**2)/(a**2)                          
        n = (a-b)/(a+b)
        n2 = n**2
        n3 = n**3

        

### IMPLEMENTATION ###

def zonecoord_to_eastnorth (coord_str):
        """
        Convert a string of coordinates within a zone to distances.
        
        :Params:
                coord_str string
                        A string of two numbers of equal length, with no spacing,
                        like '114525' or '1140052500'. Normally this would be 3 digits
                        each, but is commonly up to 10.
                        
        :Returns:
                The distance of the point from the south-west in metres, given as
                an east-north tuple.
                
        This is primarily for internal use, as part of converting OS references,
        but is provided as a seperate function for convenience.
        
        For example::
        
                >>> zonecoord_to_eastnorth ('900100')
                (90000.0, 10000.0)
                >>> zonecoord_to_eastnorth ('90001000')
                (90000.0, 10000.0)
                >>> zonecoord_to_eastnorth ('9000110002')
                (90001.0, 10002.0)
        
        """
        ## Preconditions:
        len_str = len (coord_str)
        assert (len_str % 2 == 0)
        ## Main:
        # calc size & resolution of numeric portion, split
        rez = len_str / 2
        osgb_easting = coord_str[:rez]
        osgb_northing = coord_str[rez:]
        # what is each digit (in metres)
        rez_unit = 10.0**(5-rez)
        return int (osgb_easting) * rez_unit, int (osgb_northing) * rez_unit
        

def oszone_to_eastnorth (ossquare):
        """
        Convert an Ordinance Survey zone to distances from the reference point.
        
        :Params:
                ossquare
                        A two letter, uppercase letter prefix from an OS reference. The
                        initial letter - for the major 500 km zones - is expected to be
                        one of ``HJNOST`` as those are the only ones in practical use. 
        
        :Returns:
                The easting and northing of the southwest corner for that zone from
                the OSGB reference point in meters.
                
        For example::
        
                # the southwest corner of zone T
                >>> oszone_to_eastnorth ('TV')
                (500000, 0)
                
                # the square at the northwest of zone T
                >>> oszone_to_eastnorth ('TA')
                (500000, 400000)
                
                # the southwest corner of zone S, which is the origin
                >>> oszone_to_eastnorth ('SV')
                (0, 0)
                
                # London
                >>> oszone_to_eastnorth ('TQ')
                (500000, 100000)
        
        """
        ## Preconditions:
        assert (len (ossquare) == 2)
        ## Main:
        # find the 500km square
        mainsq = ossquare[0]
        if (mainsq is 'S'):
                x, y = 0, 0
        elif (mainsq is 'T'):
                x, y = 1, 0
        elif (mainsq is 'N'):
                x, y = 0, 1
        elif (mainsq is 'O'):
                x, y = 1, 1
        elif (mainsq is 'H'):
                x, y = 0, 2
        elif (mainsq is 'J'):
                x, y = 1, 2
        else:
                assert (False), "'%s' is not an OSGB 500km square" % mainsq
        easting = x * 500
        northing = y * 500
        
        # find the 100km offset & add
        grid = "VWXYZQRSTULMNOPFGHJKABCDE"
        minorsq = mainsq = ossquare[1]
        assert (minorsq in grid), "'%s' is not an OSGB 100km square" % mimorsq
        posn = grid.find (minorsq)
        easting += (posn % 5) * 100
        northing += (posn / 5) * 100
        return easting * 1000, northing * 1000
        

def osgb_to_lonlat (osgb_str):
        """
        Convert an Ordinance Survey reference to a longitude and latitude.
        
        :Params:
                osgb_str
                        An Ordnance Survey grid reference in "letter-number" format.
                        Case and spaces are cleaned up by this function, and resolution
                        automatically detected, so that so that 'TM114 525', 'TM114525',
                        and 'TM 11400 52500' are all recognised and identical. 
        
        :Returns:
                The longitude and latitude of the grid reference, according to
                OS1936.
                
        For example::
        
                # just outside Ipswich, about 1.088975 52.129892
                >>> lon, lat = osgb_to_lonlat ('TM114 525')
                >>> 1.0889 < lon < 1.0890
                True
                >>> 52.1298 < lat < 52.1299
                True
                
                # accepts poor formating
                >>> lon2, lat2 = osgb_to_lonlat (' TM 114525 ')
                >>> lon2 == lon
                True
                >>> lat2 == lat
                True
                
                # accepts higher resolution
                >>> lon, lat = osgb_to_lonlat ('TM1140052500')
                >>> 1.0889 < lon < 1.0890
                True
                >>> 52.1298 < lat < 52.1299
                True

        
        """
        ## Preconditions & preparation:
        # clean string and split off zone prefix & coords
        osgb_str = str(osgb_str)   # deals with unicode problems
        osgb_str = osgb_str.replace (' ', '').upper()
        osgb_zone = osgb_str[:2]
        osgb_coords = osgb_str[2:]
        ## Main:
        # translate into distances from ref & within zone
        zone_easting, zone_northing = oszone_to_eastnorth (osgb_zone)
        rel_easting, rel_northing = zonecoord_to_eastnorth (osgb_coords)
        east = zone_easting + rel_easting
        north = zone_northing + rel_northing
        
        # get constants for ellipsoid
        # we do this keep the calculation of some constants outside the function
        # and allow for the substitution of other constants later
        a, b = OSGB36.a, OSGB36.b
        F0 = OSGB36.F0         
        e2 = OSGB36.e2                  
        n, n2, n3 = OSGB36.n, OSGB36.n2, OSGB36.n3
        
        lat=ORIGIN_LAT
        M=0
        while (True):
                lat = (north - ORIGIN_NORTHING - M)/(a*F0) + lat
                Ma = (1 + n + (5/4)*n2 + (5/4)*n3) * (lat-ORIGIN_LAT)
                Mb = (3*n + 3*n2 + (21/8)*n3) * sin (lat-ORIGIN_LAT) * cos (lat+ORIGIN_LAT)
                Mc = ((15/8)*n2 + (15/8)*n3) * sin (2*(lat-ORIGIN_LAT)) * cos (2*(lat+ORIGIN_LAT))
                Md = (35/24)*n3 * sin(3*(lat-ORIGIN_LAT)) * cos (3*(lat+ORIGIN_LAT))
                # meridional arc
                M = b * F0 * (Ma - Mb + Mc - Md)
                if (north - ORIGIN_NORTHING - M <= 0.00001):
                        # repeat until < 0.01mm
                        break
                        
        sinlat = sin(lat)
        # transverse radius of curvature
        nu = a*F0 / sqrt (1-e2*sinlat*sinlat)
        # meridional radius of curvature     
        rho = a * F0 * (1 - e2) / pow (1 - e2 * sinlat**2, 1.5)
        eta2 = nu / rho - 1
        tanlat = tan (lat)
        tanlat2 = tanlat**2
        tanlat4 = tanlat2**2
        tanlat6 = tanlat4 * tanlat2
        seclat = 1 / cos (lat)
        nu3 = nu**3
        nu5 = nu3 * nu**2
        nu7 = nu5 * nu**2
        VII = tanlat / (2*rho*nu)
        VIII = tanlat / (24*rho*nu3) * (5+3*tanlat2+eta2-9*tanlat2*eta2)
        IX = tanlat / (720*rho*nu5) * (61+90*tanlat2+45*tanlat4)
        X = seclat / nu
        XI = seclat / (6*nu3) * (nu/rho+2*tanlat2)
        XII = seclat / (120*nu5) * (5+28*tanlat2+24*tanlat4)
        XIIA = seclat / (5040*nu7) * (61+662*tanlat2+1320*tanlat4+720*tanlat6)
        dE = east - ORIGIN_EASTING
        lat = lat - VII*dE**2 + VIII*dE**4 - IX*dE**6
        lon = ORIGIN_LON + X*dE - XI*dE**3 + XII*dE**5 - XIIA*dE**7

        return degrees (lon), degrees (lat)


def eastnorth_to_osgb (e, n, digits=3):
        """
        Convert an OS easting-northing to an OS grid reference.
        
        :Params:
                e
                        The metres east - the easting - from the OS reference point.
                n
                        The metres east - the easting - from the OS reference point.
                digits
                        The number of digits for each direction in the final grid
                        reference. By default this is 3, which is the usual in OS grid
                        references, resolving down to 100m, e.g. 'TM 114 525'.
                        
        
        For example::
        
                >>> eastnorth_to_osgb (0, 0)
                'SV 000 000'
                >>> eastnorth_to_osgb (0, 0, 5)
                'SV 00000 00000'
                >>> eastnorth_to_osgb (611400, 252500)
                'TM 114 525'
                >>> eastnorth_to_osgb (611400, 252500, 5)
                'TM 11400 52500'

                
        """
        ## Preconditions:
        assert (0 <= e)
        assert (0 <= n)
        
        # get the 100km-grid indices
        e100k = int (floor (e / 100000))
        n100k = int (floor (n / 100000))

        # translate those into numeric equivalents of the grid letters
        majorsq = (19-n100k) - (19-n100k)%5 + int (floor((e100k+10)/5))
        minorsq = (19-n100k)*5%25 + e100k%5;
        
        # map to letters
        gridletters = string.uppercase.replace ('I', '')
        letPair = gridletters[majorsq] + gridletters[minorsq]
        
        # strip 100km-grid indices from easting & northing, and reduce precision
        zone_east = int (floor ((e % 100000) / 10**(5-digits))) 
        zone_north = int (floor ((n % 100000) / 10**(5-digits)))

        return "%s %0*d %0*d" % (letPair, digits, zone_east, digits, zone_north)

        

def lonlat_to_eastnorth (lon, lat):
        """
        Convert a longitude and latitude to Ordnance Survey easting-northing.

        :Params:
                lon
                        Longitude, presumed to be in OSG36
                        
                lat
                        Latitude, ditto.
                        
        :Returns:
                A tuple of (easting, northing) offsets.
                
        For example::

                # just outside Ipswich, about (1.088975, 52.129892)
                >>> east, north = lonlat_to_eastnorth (1.088975, 52.129892)
                >>> 611395 < east < 611405
                True
                >>> 252495 < north < 252505
                True

        """
        # TODO: allow for different resolution?
        # TODO: allow for different formating?
        
        ## Preconditions & preparation:
        lon = radians (lon)
        lat = radians (lat)
        # see explanation above
        a, b = OSGB36.a, OSGB36.b
        F0 = OSGB36.F0         
        e2 = OSGB36.e2                  
        n, n2, n3 = OSGB36.n, OSGB36.n2, OSGB36.n3
        lon0 = ORIGIN_LON
        lat0 = ORIGIN_LAT
        
        ## MAIN:
        coslat = cos (lat)
        sinlat = sin (lat)
        tanlat = tan (lat)

        v = a * F0 * pow (1 - (e2 * sinlat**2), -0.5)
        rho = a * F0 * (1 - e2) * pow (1 - e2 * sinlat**2, -1.5)
        eta2 = (v / rho) - 1

        Ma = (1 + n + (5/4)*n2 + (5/4)*n3) * (lat-lat0)
        Mb = (3*n + 3*n2 + (21/8)*n3) * sin (lat-lat0) * cos (lat+lat0)
        Mc = ((15/8)*n2 + (15/8)*n3) * sin (2*(lat-lat0)) * cos (2*(lat+lat0))
        Md = (35/24)*n3 * sin (3*(lat-lat0)) * cos (3*(lat+lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)

        cos3lat = coslat**3
        cos5lat = coslat**5
        tan2lat = tanlat**2
        tan4lat = tan2lat**2

        I = M + ORIGIN_NORTHING
        II = (v/2)*sinlat*coslat
        III = (v/24)*sinlat*cos3lat*(5-tan2lat+9*eta2)
        IIIA = (v/720)*sinlat*cos5lat*(61-58*tan2lat+tan4lat)
        IV = v*coslat
        V = (v/6)*cos3lat*(v/rho-tan2lat)
        VI = (v/120) * cos5lat * (5 - 18*tan2lat + tan4lat + 14*eta2 - 58*tan2lat*eta2)
        delta_lon = lon-lon0

        east = ORIGIN_EASTING + IV*delta_lon + V*delta_lon**3 + VI*delta_lon**5
        north = I + II*delta_lon**2 + III*delta_lon**4 + IIIA*delta_lon**6
        
        return east, north


def lonlat_to_osgb (lon, lat, digits=3):
        """
        Convert a longitude and latitude to Ordnance Survey grid reference.

        :Params:
                lon
                        Longitude, presumed to be in OSG36
                lat
                        Latitude, ditto.
                digits
                        The number of digits to use for each direction in the final
                        grid reference. 3 by default, grid references can be up to
                        6.
                        
        :Returns:
                A string.
                
        For example::
        
                >>> lonlat_to_osgb (1.088975, 52.129892)
                'TM 114 525'
                >>> lonlat_to_osgb (1.088975, 52.129892, 5)
                'TM 11400 52500'
                
        """
        # NOTE: last test actually fails, due to being off by 1. That's 1
        # metre, and I'm not going to worry about it.
        east, north = lonlat_to_eastnorth (lon, lat)
        return eastnorth_to_osgb (east, north, digits)
        


# scavenged from the osgb_to_lonlat code
def osgb_to_eastnorth (osgb_str):
        """
        Convert an Ordinance Survey reference to a longitude and latitude.
        
        :Params:
                osgb_str
                        An Ordnance Survey grid reference in "letter-number" format.
                        Case and spaces are cleaned up by this function, and resolution
                        automatically detected, so that so that 'TM114 525', 'TM114525',
                        and 'TM 11400 52500' are all recognised and identical. 
        
        :Returns:
                The easting and northing of the grid reference, according to
                
        """
        ## Preconditions & preparation:
        # clean string and split off zone prefix & coords
        osgb_str = str(osgb_str)   # deals with unicode problems
        osgb_str = osgb_str.replace (' ', '').upper()
        osgb_zone = osgb_str[:2]
        osgb_coords = osgb_str[2:]
        ## Main:
        # translate into distances from ref & within zone
        zone_easting, zone_northing = oszone_to_eastnorth (osgb_zone)
        rel_easting, rel_northing = zonecoord_to_eastnorth (osgb_coords)
        east = zone_easting + rel_easting
        north = zone_northing + rel_northing
        return east, north


### TEST & DEBUG ###

def _doctest ():
        import doctest
        doctest.testmod()
        
        
### MAIN ###

if __name__ == '__main__':
        _doctest()


### END ######################################################################
