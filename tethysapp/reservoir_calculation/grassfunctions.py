import os
import sys
import subprocess
import tempfile
from tempfile import mkstemp

# Apache should have ownership and full permission over this path
DEM_FULL_PATH = "/home/sherry/DR/dr3857.tif"
DEM_NAME = 'dr3857' # DEM layer name, no extension (no .tif)
GISBASE = "/usr/lib/grass76" # full path to GRASS installation
GRASS7BIN = "grass" # command to start GRASS from shell
GISDB = os.path.join(tempfile.gettempdir(), 'grassdata')
OUTPUT_DATA_PATH = os.path.join(tempfile.gettempdir(), 'grassdata', "output_data")
os.environ["HOME"] = "/tmp"


def RC(jobid, boundary_geojson, xlon, ylat, water_level, prj):
    dem_full_path = DEM_FULL_PATH
    dem = DEM_NAME
    gisbase = GISBASE
    grass7bin = GRASS7BIN

    # Define grass data folder, location, mapset
    gisdb = GISDB
    if not os.path.exists(gisdb):
        os.mkdir(gisdb)
    location = "location_rc_{0}".format(dem)
    mapset = "PERMANENT"
    msg = ""

    output_data_path = OUTPUT_DATA_PATH
    if not os.path.exists(output_data_path):
        os.mkdir(output_data_path)

    try:
        # Create location
        location_path = os.path.join(gisdb, location)
        if not os.path.exists(location_path):
            startcmd = grass7bin + ' -c ' + dem_full_path + ' -e ' + location_path

            p = subprocess.Popen(startcmd, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                print >> sys.stderr, 'ERROR: %s' % err
                print >> sys.stderr, 'ERROR: Cannot generate location (%s)' % startcmd
                sys.exit(-1)

        # Set GISBASE environment variable
        os.environ['GISBASE'] = gisbase
        # the following not needed with trunk
        os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'bin')
        # Set GISDBASE environment variable
        os.environ['GISDBASE'] = gisdb

        # define GRASS-Python environment
        gpydir = os.path.join(gisbase, "etc", "python")
        sys.path.append(gpydir)

        # import GRASS Python bindings (see also pygrass)
        import grass.script as gscript
        import grass.script.setup as gsetup
        gscript.core.set_raise_on_error(True)

        # launch session
        gsetup.init(gisbase, gisdb, location, mapset)

        water_level = float(water_level)
        xlon = float(xlon)
        ylat = float(ylat)

        # Project xlon, ylat wgs84 into current
        if prj.lower() != "native" or prj.lower() == "wgs84":
            stats = gscript.read_command('m.proj', coordinates=(xlon, ylat), flags='i')
            coor_list = stats.split("|")
            xlon = float(coor_list[0])
            ylat = float(coor_list[1])

        # Check the dem file, import if not exist
        dem_mapset_path = os.path.join(gisdb, location, mapset, "cell", dem)

        if not os.path.exists(dem_mapset_path):
            stats = gscript.read_command('r.in.gdal', flags='o', input=dem_full_path, output=dem)

        # Define region
        stats = gscript.parse_command('g.region', raster=dem, flags='p')

        # Read extent of the dem file
        for key in stats:
            if "north:" in key:
                north = float(key.split(":")[1])
            elif "south:" in key:
                south = float(key.split(":")[1])
            elif "west:" in key:
                west = float(key.split(":")[1])
            elif "east:" in key:
                east = float(key.split(":")[1])
            elif "nsres:" in key:
                nsres = float(key.split(":")[1])
            elif "ewres:" in key:
                ewres = float(key.split(":")[1])

        # check if xlon, ylat is within the extent of dem
        if xlon < west or xlon > east:
            raise Exception("(xlon, ylat) is out of dem region.")
        elif ylat < south or ylat > north:
            raise Exception("(xlon, ylat) is out of dem region.")

        # Calculate cell area
        cell_area = nsres * ewres
        point_coordinates = (xlon,ylat)

        # write boundary_geojson content to geojson file
        fd, boundary_geojson_file_path = mkstemp()
        os.write(fd, boundary_geojson)
        os.close(fd)
        #import geojoson
        boundary_vect="boundary_vect_{0}".format(jobid)
        stats = gscript.parse_command('v.import', input=boundary_geojson_file_path, output=boundary_vect, flags='o', overwrite=True)

        #convert boundary vect to rast
        boundary_rast = "boundary_rast_{0}".format(jobid)
        stats = gscript.parse_command('v.to.rast', input=boundary_vect,output=boundary_rast,use="attr",attribute_column="cat",overwrite=True)

        # Cut dem with polygon
        dem_cropped = "{0}_{1}_cropped".format(dem, jobid)
        mapcalc_cmd = '{0} = if({1}, {2})'.format(dem_cropped, boundary_rast, dem)
        gscript.mapcalc(mapcalc_cmd, overwrite=True, quiet=True)

        # Read pour point elevation
        point_info = gscript.read_command('r.what', map=dem, coordinates=point_coordinates)
        point_elev = point_info.split('||')[1]
        try:
            point_elev = float(point_elev)
        except Exception as e:
            raise Exception("This point has no data.")

        water_top =point_elev + float(water_level)

        # Generate reservoir raster file
        lake_rast = '{0}_{1}_lake_{2}'.format(dem, jobid, str(int(water_top)))
        stats = gscript.read_command('r.lake', elevation=dem_cropped, coordinates=point_coordinates, waterlevel=water_top, lake=lake_rast, overwrite=True)

        #Calculate reservoir volume
        stats = gscript.parse_command('r.univar', map=lake_rast, flags='g')
        sum_height = float(stats['sum'])
        lake_volume = sum_height * cell_area

        # output lake
        # r.mapcalc expression="lake_285.7846_all_0 = if( lake_285.7846, 0)" --o
        lake_rast_all = "{0}_all".format(lake_rast)
        mapcalc_cmd = '{0} = if({1}, 0)'.format(lake_rast_all, lake_rast)
        gscript.mapcalc(mapcalc_cmd, overwrite=True, quiet=True)

        # covert raster lake_rast_all into vector
        # r.to.vect input='lake_285.7846_all@drew' output='lake_285_all_vec' type=area --o
        lake_rast_all_vec = "{0}_all_vect".format(lake_rast)
        lake_rast_all_vec = lake_rast_all_vec.replace(".", "_")
        stats = gscript.parse_command('r.to.vect', input=lake_rast_all, output=lake_rast_all_vec, type="area", overwrite=True)

        # output GeoJSON
        # v.out.ogr -c input='lake_285_all_vec' output='/tmp/lake_285_all_vec.geojson' format=GeoJSON type=area --overwrite
        geojson_f_name = "{0}.GEOJSON".format(lake_rast.replace(".", "_"))
        lake_rast_all_vec_GEOJSON = os.path.join(output_data_path, geojson_f_name)
        stats = gscript.parse_command('v.out.ogr', input=lake_rast_all_vec, output=lake_rast_all_vec_GEOJSON, \
                                      format="GeoJSON", type="area", overwrite=True, flags="c")

        return {"lake_volume": lake_volume,
                "lake_GEOJSON": lake_rast_all_vec_GEOJSON,
                "msg": msg,
                "status": "success"}

    except Exception as e:
        msg = e.message
        return {"lake_volume": None,
                "lake_GEOJSON": None,
                "msg": msg,
                "status": "error"}

