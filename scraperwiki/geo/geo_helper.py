# Geographical helper functions for nmea_info.py and friends
#
# Helps with geographic functions, including:
#  Lat+Long+Height -> XYZ
#  XYZ -> Lat+Long+Height
#  Lat+Long -> other Lat+Long (Helmert Transform)
#  Lat+Long -> easting/northing (OS GB+IE Only)
#  easting/northing -> Lat+Long (OS GB+IE Only)
#  OS easting/northing -> OS 6 figure ref
#
# See http://gagravarr.org/code/ for updates and information
#
# GPL
#
# Nick Burch - v0.06 (30/05/2007)

import math

# For each co-ordinate system we do, what are the A, B and E2 values?
# List is A, B, E^2 (E^2 calculated after)
abe_values = {
        'wgs84': [ 6378137.0, 6356752.3141, -1 ],
        'osgb' : [ 6377563.396, 6356256.91, -1 ],
        'osie' : [ 6377340.189, 6356034.447, -1 ]
}

# The earth's radius, in meters, as taken from an average of the WGS84
#  a and b parameters (should be close enough)
earths_radius = (abe_values['wgs84'][0] + abe_values['wgs84'][1]) / 2.0

# Calculate the E2 values
for system in abe_values.keys():
        a = abe_values[system][0]
        b = abe_values[system][1]
        e2 = (a*a - b*b) / (a*a)
        abe_values[system][2] = e2

# For each co-ordinate system we can translate between, what are
#  the tx, ty, tz, s, rx, ry and rz values?
# List is tx, ty, tz, s, rx, ry, rz
transform_values = {
        'wgs84_to_osgb' : [ -446.448, 125.157, -542.060, 
                                                        20.4894 / 1000.0 / 1000.0, # given as ppm
                                                        -0.1502 / 206265.0, # given as seconds of arc
                                                        -0.2470 / 206265.0, # given as seconds of arc
                                                        -0.8421 / 206265.0  # given as seconds of arc
                                        ],
        'wgs84_to_osie' : [ -482.530, 130.596, -564.557, 
                                                        -8.1500 / 1000.0 / 1000.0, # given as ppm
                                                        -1.0420 / 206265.0, # given as seconds of arc
                                                        -0.2140 / 206265.0, # given as seconds of arc
                                                        -0.6310 / 206265.0  # given as seconds of arc
                                        ],
        'itrs2000_to_etrs89' : [ 0.054, 0.051, -0.048, 0,
                                                         0.000081 / 206265.0, # given as seconds of arc
                                                         0.00049 / 206265.0, # given as seconds of arc
                                                         0.000792 / 206265.0  # given as seconds of arc
                                        ]
}

# Calculate reverse transforms
for systems in [('wgs84','osgb'), ('wgs84','osie'), ('itrs2000','etrs89')]:
        fs = systems[0] + "_to_" + systems[1]
        rs = systems[1] + "_to_" + systems[0]
        ra = []
        for val in transform_values[fs]:
                ra.append(-1.0 * val)
        transform_values[rs] = ra

# Easting and Northin system values, for the systems we work with.
# List is n0, e0, F0, theta0 and landa0
en_values = {
        'osgb' : [ -100000.0, 400000.0, 0.9996012717,
                                        49.0 /360.0 *2.0*math.pi,
                                        -2.0 /360.0 *2.0*math.pi
                         ],
        'osie' : [ 250000.0, 200000.0, 1.000035,
                                        53.5 /360.0 *2.0*math.pi,
                                        -8.0 /360.0 *2.0*math.pi
                         ]
}

# Cassini Projection Origins
# List is lat (rad), long (rad), false easting, false northing
cassini_values = {
        'osgb' : [ (53.0 + (13.0 / 60.0) + (17.274 / 3600.0)) /360.0 *2.0*math.pi,
                   -(2.0 + (41.0 / 60.0) +  (3.562 / 3600.0)) /360.0 *2.0*math.pi,
                   0, 0 ]                                
}

# How many feet to the meter
feet_per_meter = 1.0 / 0.3048007491   # 3.28083

##############################################################
#         OS GB Specific Helpers for Generic Methods         #
##############################################################

def turn_wgs84_into_osgb36(lat_dec,long_dec,height):
        """See http://www.gps.gov.uk/guide6.asp#6.2 and http://www.gps.gov.uk/guide6.asp#6.6 for the calculations, and http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34h.html for some background."""

        wgs84_xyz = turn_llh_into_xyz(lat_dec,long_dec,height,'wgs84')

        osgb_xyz = turn_xyz_into_other_xyz(
                                        wgs84_xyz[0],wgs84_xyz[1],wgs84_xyz[2],'wgs84','osgb')

        osgb_latlong = turn_xyz_into_llh(
                                        osgb_xyz[0],osgb_xyz[1],osgb_xyz[2],'osgb')
        return osgb_latlong

def turn_osgb36_into_wgs84(lat_dec,long_dec,height):
        """See http://www.gps.gov.uk/guide6.asp#6.2 and http://www.gps.gov.uk/guide6.asp#6.6 for the calculations, and http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34h.html for some background."""

        osgb_xyz = turn_llh_into_xyz(lat_dec,long_dec,height,'osgb')

        wgs84_xyz = turn_xyz_into_other_xyz(
                                        osgb_xyz[0],osgb_xyz[1],osgb_xyz[2],'osgb','wgs84')

        wgs84_latlong = turn_xyz_into_llh(
                                        wgs84_xyz[0],wgs84_xyz[1],wgs84_xyz[2],'wgs84')

        return wgs84_latlong

def turn_osgb36_into_eastingnorthing(lat_dec,long_dec):
        """Turn OSGB36 (decimal) lat/long values into OS easting and northing values."""
        return turn_latlong_into_eastingnorthing(lat_dec,long_dec,'osgb')

def turn_eastingnorthing_into_osgb36(easting,northing):
        """Turn OSGB36 easting and northing values into (decimal) lat/long values inOSGB36."""
        return turn_eastingnorthing_into_latlong(easting,northing,'osgb')

##############################################################
#         OS IE Specific Helpers for Generic Methods         #
##############################################################

def turn_wgs84_into_osie36(lat_dec,long_dec,height):
        """As per turn_wgs84_into_osgb36, but for Irish grid"""

        wgs84_xyz = turn_llh_into_xyz(lat_dec,long_dec,height,'wgs84')

        osie_xyz = turn_xyz_into_other_xyz(
                                        wgs84_xyz[0],wgs84_xyz[1],wgs84_xyz[2],'wgs84','osie')

        osie_latlong = turn_xyz_into_llh(
                                        osie_xyz[0],osie_xyz[1],osie_xyz[2],'osie')
        return osie_latlong

def turn_osie36_into_wgs84(lat_dec,long_dec,height):
        """As per turn_osgb36_into_wgs84, but for Irish grid"""

        osie_xyz = turn_llh_into_xyz(lat_dec,long_dec,height,'osie')

        wgs84_xyz = turn_xyz_into_other_xyz(
                                        osie_xyz[0],osie_xyz[1],osie_xyz[2],'osie','wgs84')

        wgs84_latlong = turn_xyz_into_llh(
                                        wgs84_xyz[0],wgs84_xyz[1],wgs84_xyz[2],'wgs84')

        return wgs84_latlong

def turn_osie36_into_eastingnorthing(lat_dec,long_dec):
        """Turn OSIE36 (decimal) lat/long values into OS IE easting and northing values."""
        return turn_latlong_into_eastingnorthing(lat_dec,long_dec,'osie')

def turn_eastingnorthing_into_osie36(easting,northing):
        """Turn OSIE36 easting and northing values into (decimal) lat/long values inOSIE36."""
        return turn_eastingnorthing_into_latlong(easting,northing,'osie')

##############################################################
#             Generic Transform Functions                    #
##############################################################

def turn_llh_into_xyz(lat_dec,long_dec,height,system):
        """Convert Lat, Long and Height into 3D Cartesian x,y,z
       See http://www.ordnancesurvey.co.uk/gps/docs/convertingcoordinates3D.pdf"""

        a = abe_values[system][0]
        b = abe_values[system][1]
        e2 = abe_values[system][2]

        theta = float(lat_dec)  / 360.0 * 2.0 * math.pi
        landa = float(long_dec) / 360.0 * 2.0 * math.pi
        height = float(height)

        v = a / math.sqrt( 1.0 - e2 * (math.sin(theta) * math.sin(theta)) )
        x = (v + height) * math.cos(theta) * math.cos(landa)
        y = (v + height) * math.cos(theta) * math.sin(landa)
        z = ( (1.0 - e2) * v + height ) * math.sin(theta)

        return [x,y,z]

def turn_xyz_into_llh(x,y,z,system):
        """Convert 3D Cartesian x,y,z into Lat, Long and Height
       See http://www.ordnancesurvey.co.uk/gps/docs/convertingcoordinates3D.pdf"""

        a = abe_values[system][0]
        b = abe_values[system][1]
        e2 = abe_values[system][2]

        p = math.sqrt(x*x + y*y)

        long = math.atan(y/x)
        lat_init = math.atan( z / (p * (1.0 - e2)) )
        v = a / math.sqrt( 1.0 - e2 * (math.sin(lat_init) * math.sin(lat_init)) )
        lat = math.atan( (z + e2*v*math.sin(lat_init)) / p )

        height = (p / math.cos(lat)) - v # Ignore if a bit out

        # Turn from radians back into degrees
        long = long / 2 / math.pi * 360
        lat = lat / 2 / math.pi * 360

        return [lat,long,height]

def turn_xyz_into_other_xyz(old_x,old_y,old_z,from_scheme,to_scheme):
        """Helmert Transformation between one lat+long system and another
See http://www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/guide6.html for the calculations, and http://www.movable-type.co.uk/scripts/LatLongConvertCoords.html for a friendlier version with examples"""

        transform = from_scheme + "_to_" + to_scheme
        tx = transform_values[transform][0]
        ty = transform_values[transform][1]
        tz = transform_values[transform][2]
        s =  transform_values[transform][3]
        rx = transform_values[transform][4]
        ry = transform_values[transform][5]
        rz = transform_values[transform][6]

        # Do the transform
        new_x = tx + ((1.0+s) * old_x) + (-rz * old_y) + (ry * old_z)
        new_y = ty + (rz * old_x) + ((1.0+s) * old_y) + (-rx * old_z)
        new_z = tz + (-ry * old_x) + (rx * old_y) + ((1.0+s) * old_z)

        return [new_x,new_y,new_z]

def calculate_distance_and_bearing(from_lat_dec,from_long_dec,to_lat_dec,to_long_dec):
        """Uses the spherical law of cosines to calculate the distance and bearing between two positions"""

        # Turn them all into radians
        from_theta = float(from_lat_dec)  / 360.0 * 2.0 * math.pi
        from_landa = float(from_long_dec) / 360.0 * 2.0 * math.pi
        to_theta = float(to_lat_dec)  / 360.0 * 2.0 * math.pi
        to_landa = float(to_long_dec) / 360.0 * 2.0 * math.pi

        d = math.acos(
                        math.sin(from_theta) * math.sin(to_theta) +
                        math.cos(from_theta) * math.cos(to_theta) * math.cos(to_landa-from_landa)
                ) * earths_radius

        bearing = math.atan2(
                        math.sin(to_landa-from_landa) * math.cos(to_theta),
                        math.cos(from_theta) * math.sin(to_theta) -
                        math.sin(from_theta) * math.cos(to_theta) * math.cos(to_landa-from_landa)
                )
        bearing = bearing / 2.0 / math.pi * 360.0

        return [d,bearing]

##############################################################
#            Easting/Northing Transform Methods              #
##############################################################

def turn_latlong_into_eastingnorthing(lat_dec,long_dec,scheme):
        """Turn OSGB36 or OSIE36 (decimal) lat/long values into OS easting and northing values. See http://www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/guide7.html for the calculations, and http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34h.html for some background."""

        n0 = en_values[scheme][0]
        e0 = en_values[scheme][1]
        f0 = en_values[scheme][2]

        theta0 = en_values[scheme][3]
        landa0 = en_values[scheme][4]

        a = abe_values[scheme][0]
        b = abe_values[scheme][1]
        e2 = abe_values[scheme][2]

        theta = float(lat_dec)  /360.0 *2.0*math.pi
        landa = float(long_dec) /360.0 *2.0*math.pi

        n = (a-b) / (a+b)
        v = a * f0 * math.pow( (1 - e2 * math.sin(theta)*math.sin(theta)), -0.5 )
        ro = a * f0 * (1 - e2) * math.pow( (1 - e2 * math.sin(theta)*math.sin(theta)), -1.5 )
        nu2 = v/ro - 1

        M = b * f0 * ( \
                (1.0 + n + 5.0/4.0 *n*n + 5.0/4.0 *n*n*n) * (theta-theta0) - \
                (3.0*n + 3.0*n*n + 21.0/8.0 *n*n*n) *math.sin(theta-theta0) *math.cos(theta+theta0) + \
                (15.0/8.0*n*n + 15.0/8.0*n*n*n) *math.sin(2.0*(theta-theta0)) *math.cos(2.0*(theta+theta0)) - \
                35.0/24.0*n*n*n *math.sin(3.0*(theta-theta0)) *math.cos(3.0*(theta+theta0)) \
        )

        I = M + n0
        II = v/2.0 * math.sin(theta) * math.cos(theta)
        III = v/24.0 * math.sin(theta) * math.pow( math.cos(theta),3 ) * \
                (5.0 - math.pow(math.tan(theta),2) + 9.0*nu2)
        IIIa = v/720.0 * math.sin(theta) * math.pow( math.cos(theta),5 ) * \
                ( 61.0 - 58.0 *math.pow(math.tan(theta),2) + math.pow(math.tan(theta),4) )
        IV = v * math.cos(theta)
        V = v/6.0 * math.pow( math.cos(theta),3 ) * \
                ( v/ro - math.pow(math.tan(theta),2) )
        VI = v/120.0 * math.pow(math.cos(theta),5) * \
                ( 5.0 - 18.0 *math.pow(math.tan(theta),2) + \
                math.pow(math.tan(theta),4) + 14.0*nu2 - \
                58.0 * math.pow(math.tan(theta),2)*nu2 )

        northing = I + II*math.pow(landa-landa0,2) + \
                III*math.pow(landa-landa0,4) + \
                IIIa*math.pow(landa-landa0,6)
        easting = e0 + IV*(landa-landa0) + V*math.pow(landa-landa0,3) + \
                VI*math.pow(landa-landa0,5)
        
        return (easting,northing)

def turn_eastingnorthing_into_latlong(easting,northing,scheme):
        """Turn OSGB36 or OSIE36 easting and northing values into (decimal) lat/long values in OSGB36 / OSIE36. See http://www.ordnancesurvey.co.uk/oswebsite/gps/information/coordinatesystemsinfo/guidecontents/guide7.html for the calculations, and http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34h.html for some background."""

        n0 = en_values[scheme][0]
        e0 = en_values[scheme][1]
        f0 = en_values[scheme][2]

        theta0 = en_values[scheme][3]
        landa0 = en_values[scheme][4]

        a = abe_values[scheme][0]
        b = abe_values[scheme][1]
        e2 = abe_values[scheme][2]

        n = (a-b) / (a+b)

        # Prepare to iterate
        M = 0
        theta = theta0
        # Iterate, 4 times should be enough
        for i in range(4):
                theta = ((northing - n0 - M) / (a * f0)) + theta
                M = b * f0 * ( \
                        (1.0 + n + 5.0/4.0 *n*n + 5.0/4.0 *n*n*n) * (theta-theta0) - \
                        (3.0*n + 3.0*n*n + 21.0/8.0 *n*n*n) *math.sin(theta-theta0) *math.cos(theta+theta0) + \
                        (15.0/8.0*n*n + 15.0/8.0*n*n*n) *math.sin(2.0*(theta-theta0)) *math.cos(2.0*(theta+theta0)) - \
                        35.0/24.0*n*n*n *math.sin(3.0*(theta-theta0)) *math.cos(3.0*(theta+theta0)) \
                )

        # Compute intermediate values
        v = a * f0 * math.pow( (1 - e2 * math.sin(theta)*math.sin(theta)), -0.5 )
        ro = a * f0 * (1 - e2) * math.pow( (1 - e2 * math.sin(theta)*math.sin(theta)), -1.5 )
        nu2 = v/ro - 1
        tantheta2 = math.pow(math.tan(theta),2)

        VII = math.tan(theta) / (2 * ro * v)
        VIII = math.tan(theta) / (24 * ro * math.pow(v,3)) \
                        * (5 + 3 * tantheta2 + nu2 - \
                           9 * tantheta2 *  nu2 )
        IX = math.tan(theta) / (720 * ro * math.pow(v,5)) \
                        * (61 + 90 * tantheta2 + 45 * tantheta2 * tantheta2)
        X = 1 / (math.cos(theta) * v)
        XI = 1 / (math.cos(theta) * 6 * math.pow(v,3)) \
                        * (v/ro + 2*tantheta2)
        XII = 1 / (math.cos(theta) * 120 * math.pow(v,5)) \
                        * (5 + 28 * tantheta2 + 24 * tantheta2 * tantheta2)
        XIIa = 1 / (math.cos(theta) * 5040 * math.pow(v,7)) \
                        * (61 + 662 * tantheta2 + 1320 * tantheta2 * tantheta2 \
                                + 720 * tantheta2 * tantheta2 * tantheta2)

        lat_rad = theta - VII * math.pow((easting-e0),2) \
                                + VIII * math.pow((easting-e0),4) \
                                - IX * math.pow((easting-e0),6)
        long_rad = landa0 + X * (easting-e0) \
                                - XI * math.pow((easting-e0),3) \
                                + XII * math.pow((easting-e0),5) \
                                - XIIa * math.pow((easting-e0),7)

        lat = lat_rad / 2.0 / math.pi * 360.0
        long = long_rad / 2.0 / math.pi * 360.0

        return (lat,long)

##############################################################
#         Cassini Easting/Northing Transform Methods         #
##############################################################

def turn_latlong_into_cassini_en(lat_dec,long_dec,scheme):
        """Latitude and Longitude, into Cassini-Soldner easting and northing co-ordinates, in the given scheme. See http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34g.html for details of the calculation used"""
        
        a = abe_values[scheme][0]
        b = abe_values[scheme][1]
        e2 = abe_values[scheme][2]

        e4 = e2 * e2
        e6 = e2 * e2 * e2

        theta = float(lat_dec)  /360.0 *2.0*math.pi
        landa = float(long_dec) /360.0 *2.0*math.pi

        theta0 = cassini_values[scheme][0]
        landa0 = cassini_values[scheme][1]
        false_easting = cassini_values[scheme][2]
        false_northing = cassini_values[scheme][3]

        # Compute intermediate values
        A = (landa - landa0) * math.cos(theta)
        T = math.tan(theta) * math.tan(theta)
        C = e2 / (1.0 - e2) * math.cos(theta) * math.cos(theta)
        v = a / math.sqrt( 1 - (e2 * math.sin(theta) * math.sin(theta)) )

        A2 = A ** 2
        A3 = A ** 3
        A4 = A ** 4
        A5 = A ** 5

        # And M, which is how far along the meridian our latitude is from the origin
        def makeM(picked_theta):
                return a * (
                        (1.0 - e2/4.0 - 3.0*e4/64.0 - 5.0*e6/256.0) * picked_theta
                  - (3.0*e2/8.0 + 3.0*e4/32.0 + 45.0*e6/1024.0) * math.sin(2.0*picked_theta)
                  + (15.0*e4/256.0 + 45.0*e6/1024.0) * math.sin(4.0*picked_theta)
                  - (35.0*e6/3072.0) * math.sin(6.0*picked_theta)
            )
        M = makeM(theta)
        M0 = makeM(theta0)

        # Now calculate
        easting = false_easting + v * (
                                A - T * A3 / 6.0 - (8.0 - T + 8.0*C) * T * A5 / 120.0 )
        northing = false_northing + M - M0 + v * math.tan(theta) * (
                                A2 / 2.0 + (5.0 - T + 6.0*C) * A4 / 24.0 )

        return (easting,northing)

def turn_cassini_en_into_latlong(easting,northing,scheme):
        """Cassini-Soldner easting and northing, into Latitude and Longitude, in the given scheme. See http://www.posc.org/Epicentre.2_2/DataModel/ExamplesofUsage/eu_cs34g.html for details of the calculation used"""
        
        a = abe_values[scheme][0]
        b = abe_values[scheme][1]
        e2 = abe_values[scheme][2]

        e4 = e2 * e2
        e6 = e2 * e2 * e2

        theta0 = cassini_values[scheme][0]
        landa0 = cassini_values[scheme][1]
        false_easting = cassini_values[scheme][2]
        false_northing = cassini_values[scheme][3]

        def makeM(picked_theta):
                return a * (
                        (1.0 - e2/4.0 - 3.0*e4/64.0 - 5.0*e6/256.0) * picked_theta
                  - (3.0*e2/8.0 + 3.0*e4/32.0 + 45.0*e6/1024.0) * math.sin(2.0*picked_theta)
                  + (15.0*e4/256.0 + 45.0*e6/1024.0) * math.sin(4.0*picked_theta)
                  - (35.0*e6/3072.0) * math.sin(6.0*picked_theta)
            )

        # Compute first batch of intermediate values
        M1 = makeM(theta0) + (northing - false_northing)
        mu1 = M1 / (a * (1.0 - e2/4.0 - 3.0*e4/64.0 - 5.0*e6/256.0) )
        e1 = (1 - ((1-e2) ** 0.5)) / (1 + ((1-e2) ** 0.5))

        e1_2 = e1 ** 2
        e1_3 = e1 ** 3
        e1_4 = e1 ** 4

        # Now compute theta1 at T1
        theta1 = mu1 + (
        + (3.0*e1 / 2.0 - 27.0*e1_3 / 32.0) * math.sin(2.0*mu1)
        + (21.0*e1_2 / 16.0 - 55.0*e1_4 / 32.0) * math.sin(4.0*mu1)
        + (151.0*e1_3 / 96.0) * math.sin(6.0*mu1)
        + (1097.0*e1_4 / 512.0) * math.sin(8.0*mu1) 
        )
        T1 = (math.tan(theta1)) ** 2

        # Now we can find v1, ro1 and D
        v1 = a / math.sqrt( 1.0 - (e2 * math.sin(theta1) * math.sin(theta1)) )
        ro1 = a * (1 - e2) / ((1 - e2 * math.sin(theta1) * math.sin(theta1)) ** 1.5)
        D = (easting - false_easting) / v1

        # And finally the lat and long
        lat = theta1 - (v1 * math.tan(theta1)) / ro1 * (
                        D*D/2.0 - (1.0 + 3.0 * T1) * ( (D**4) / 24.0 ) )
        long = landa0 + (
                                D - T1 * (D**3) / 3.0 + (1 + 3.0 * T1) * T1 * (D**5) / 15.0
                        ) / math.cos(theta1)

        # Now make decimal versions
        lat_dec = lat * 360.0 / 2.0 / math.pi
        long_dec = long * 360.0 / 2.0 / math.pi

        return (lat_dec,long_dec)

##############################################################
#             OS Specific Methods Follow                     #
##############################################################

def turn_easting_northing_into_six_fig(easting,northing):
        """Turn OS easting and northing values into the six figure OS grid refecence. See http://www.jstott.me.uk/jscoord/"""
        first_letter = ""
        second_letter = ""

        easting = int(easting)
        northing = int(northing)

        # Get the 100 km part
        hkm_east = int( math.floor(easting / 100000.0) )
        hkm_north = int( math.floor(northing / 100000.0) )
        if hkm_north < 5:
                if hkm_east < 5:
                        first_letter = "S"
                else:
                        first_letter = "T"
        elif hkm_north < 10:
                if hkm_east < 5:
                        first_letter = "N"
                else:
                        first_letter = "O"
        else:
                first_letter = "H"

        # Get the 10km part
        index = 65 + ((4 - (hkm_north % 5)) * 5) + (hkm_east % 5)
        ti = index
        if index >= 73:
                index += 1
        second_letter = chr(index)

        # Get digits 2-4 on easting and northing
        e = math.floor( (easting  - (100000.0 * hkm_east))  / 100.0)
        n = math.floor( (northing - (100000.0 * hkm_north)) / 100.0)
        e = "%03d" % e
        n = "%03d" % n

        return first_letter + second_letter + e + n
