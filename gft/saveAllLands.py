#!/usr/bin/env python3

# Define function ...
def saveAllLands(
    wName,
    dname,
    /,
    *,
    avoidCountries = [
        "Baikonur",
        "Iran",
        "Russia",
        "Ukraine",
    ],
             debug = __debug__,
              dist = -1.0,
              fill = 1.0,
         fillSpace = "EuclideanSpace",
             local = False,
          maxPlane = None,
              nAng = 9,
             nIter = 100,
             neRes = "110m",
              simp = 0.1,
               tol = 1.0e-10,
):
    """Save (optionally buffered and optionally simplified) land to a compressed
    WKB file.

    Parameters
    ----------
    wName : string
        the file name of the compressed WKB file
    dname : string
        the directory name where temporary compressed WKB files can be stored
    debug : bool, optional
        print debug messages
    dist : float, optional
        the distance to buffer the land by; negative values disable buffering
        (in metres)
    fill : float, optional
        how many intermediary points are added to fill in the straight lines
        which connect the points; negative values disable filling
    fillSpace : str, optional
        the geometric space to perform the filling in (either "EuclideanSpace"
        or "GeodesicSpace")
    local : bool, optional
        the plot has only local extent
    maxPlane : shapely.geometry.polygon.Polygon, shapely.geometry.multipolygon.MultiPolygon
        the maximum possible flying distance (ignoring all land)
    nAng : int, optional
        the number of angles around each point that are calculated when
        buffering
    neRes : string, optional
        the resolution of the Natural Earth datasets
    nIter : int, optional
        the maximum number of iterations (particularly the Vincenty formula)
    simp : float, optional
        how much intermediary [Multi]Polygons are simplified by; negative values
        disable simplification (in degrees)
    tol : float, optional
        the Euclidean distance that defines two points as being the same (in
        degrees)
    """

    # Import standard modules ...
    import glob
    import gzip
    import os
    import pathlib

    # Import special modules ...
    try:
        import cartopy
        cartopy.config.update(
            {
                "cache_dir" : pathlib.PosixPath("~/.local/share/cartopy_cache").expanduser(),
            }
        )
    except:
        raise Exception("\"cartopy\" is not installed; run \"pip install --user Cartopy\"") from None
    try:
        import geojson
    except:
        raise Exception("\"geojson\" is not installed; run \"pip install --user geojson\"") from None
    try:
        import shapely
        import shapely.geometry
        import shapely.ops
        import shapely.wkb
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    import sys
    sys.path.append("../gst")
    import gst
    try:
        import pyguymer3
        import pyguymer3.geo
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create short-hand ...
    gName = f'{wName.removesuffix(".wkb.gz")}.geojson'

    # **************************************************************************

    # Deduce Shapefile name ...
    sfile = cartopy.io.shapereader.natural_earth(
          category = "cultural",
              name = "admin_0_countries",
        resolution = neRes,
    )

    # **************************************************************************

    print(f" > Loading \"{sfile}\" ...")

    # Loop over records ...
    for record in cartopy.io.shapereader.Reader(sfile).records():
        # Create short-hand and skip this record if it is not to be avoided ...
        neName = pyguymer3.geo.getRecordAttribute(record, "NAME")
        if neName not in avoidCountries:
            continue

        # Deduce temporary file name and skip record if it exists already ...
        tmpName = f"{dname}/{record.geometry.centroid.x:+011.6f},{record.geometry.centroid.y:+010.6f},{record.geometry.area:012.7f}.wkb.gz"
        if os.path.exists(tmpName):
            continue

        print(f"   > Making \"{tmpName}\" ...")

        # Initialize list ...
        polys = []

        # Loop over Polygons ...
        for poly in pyguymer3.geo.extract_polys(
            record.geometry,
            onlyValid = True,
               repair = True,
        ):
            # Check if only Polygons local to the plane should be saved ...
            if local and maxPlane is not None:
                # Skip Polygon if it is outside of the maximum possible flying
                # distance of the plane ...
                if maxPlane.disjoint(poly):
                    continue

                # Throw away all parts of the Polygon that the plane will never
                # fly to ...
                poly = maxPlane.intersection(poly)

            # Check if the user wants to buffer the land ...
            # NOTE: The land should probably be buffered to prohibit planes
            #       jumping over narrow stretches that are narrower than the
            #       iteration distance.
            if dist > 0.0:
                # Find the buffer of the land ...
                poly = pyguymer3.geo.buffer(
                    poly,
                    dist,
                            debug = debug,
                             fill = fill,
                        fillSpace = fillSpace,
                    keepInteriors = False,
                             nAng = nAng,
                            nIter = nIter,
                             simp = simp,
                              tol = tol,
                )

            # Add the Polygons to the list ...
            # NOTE: Given how "poly" was made, we know that there aren't any
            #       invalid Polygons, so don't bother checking for them.
            polys += pyguymer3.geo.extract_polys(
                poly,
                onlyValid = False,
                   repair = False,
            )

        # Skip record if it does not have any Polygons ...
        if not polys:
            print("     > Skipped (no Polygons).")
            continue

        # Convert list of Polygons to a (unified) [Multi]Polygon ...
        polys = shapely.ops.unary_union(polys).simplify(tol)
        if debug:
            pyguymer3.geo.check(polys)

        # Save [Multi]Polygon ...
        with gzip.open(tmpName, mode = "wb", compresslevel = 9) as gzObj:
            gzObj.write(shapely.wkb.dumps(polys))

    # **************************************************************************

    # Initialize list ...
    polys = []

    # Loop over temporary compressed WKB files ...
    for tmpName in sorted(glob.glob(f"{dname}/????.??????,???.??????,????.???????.wkb.gz")):
        print(f" > Loading \"{tmpName}\" ...")

        # Add the individual Polygons to the list ...
        # NOTE: Given how "polys" was made, we know that there aren't any
        #       invalid Polygons, so don't bother checking for them.
        with gzip.open(tmpName, mode = "rb") as gzObj:
            polys += pyguymer3.geo.extract_polys(
                shapely.wkb.loads(gzObj.read()),
                onlyValid = False,
                   repair = False,
            )

    # Return if there isn't any land at this resolution ...
    if not polys:
        return False

    # Convert list of Polygons to a (unified) MultiPolygon ...
    # NOTE: Given how "polys" was made, we know that there aren't any invalid
    #       Polygons, so don't bother checking for them.
    polys = shapely.ops.unary_union(polys).simplify(tol)
    polys = gst.removeInteriorRings(
        polys,
        onlyValid = False,
           repair = False,
    )
    if debug:
        pyguymer3.geo.check(polys)

    # Check if the user wants to simplify the MultiPolygon ...
    if simp > 0.0:
        # Simplify MultiPolygon ...
        # NOTE: Given how "polys" was made, we know that there aren't any
        #       invalid Polygons, so don't bother checking for them.
        polys = polys.simplify(simp)
        polys = gst.removeInteriorRings(
            polys,
            onlyValid = False,
               repair = False,
        )
        if debug:
            pyguymer3.geo.check(polys)

    # Save MultiPolygon ...
    with gzip.open(wName, mode = "wb", compresslevel = 9) as gzObj:
        gzObj.write(shapely.wkb.dumps(polys))

    # Save MultiPolygon ...
    with open(gName, "wt", encoding = "utf-8") as fObj:
        geojson.dump(
            polys,
            fObj,
            ensure_ascii = False,
                  indent = 4,
               sort_keys = True,
        )

    # Return ...
    return True
