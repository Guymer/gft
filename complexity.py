#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import gzip
    import json
    import math
    import os
    import subprocess
    import sysconfig

    # Import special modules ...
    try:
        import numpy
    except:
        raise Exception("\"numpy\" is not installed; run \"pip install --user numpy\"") from None
    try:
        import PIL
        import PIL.Image
        PIL.Image.MAX_IMAGE_PIXELS = 1024 * 1024 * 1024                         # [px]
        import PIL.ImageDraw
    except:
        raise Exception("\"PIL\" is not installed; run \"pip install --user Pillow\"") from None
    try:
        import shapely
        import shapely.wkb
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "Show the complexity of country boundaries for different flying configurations.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--debug",
        action = "store_true",
          dest = "debug",
          help = "print debug messages",
    )
    parser.add_argument(
        "--dry-run",
        action = "store_true",
          dest = "dryRun",
          help = "don't run GFT - just assume that all the required GFT output is there already",
    )
    parser.add_argument(
        "--timeout",
        default = 60.0,
           help = "the timeout for any requests/subprocess calls (in seconds)",
           type = float,
    )
    args = parser.parse_args()

    # **************************************************************************

    # Define resolution ...
    gshhgRes = "c"

    # Define combinations ...
    combs = [
        ( 9, "110m", 116000     , (1.0, 0.0, 0.0, 1.0),),
        (17,  "50m", 116000 // 2, (0.0, 1.0, 0.0, 1.0),),
        (33,  "10m", 116000 // 4, (0.0, 0.0, 1.0, 1.0),),
    ]
    spd = 500.0                                                                 # [kts]

    # Load colour tables ...
    with open(f"{pyguymer3.__path__[0]}/data/json/colourTables.json", "rt", encoding = "utf-8") as fObj:
        cts = json.load(fObj)

    # **************************************************************************

    # Loop over combinations ...
    for nAng, neRes, prec, color in combs:
        # Create short-hands ...
        # NOTE: Say that 928,000 metres takes 1 hour at 500 knots.
        freqLand = 8 * 928000 // prec                                           # [#]
        freqPlot = 928000 // prec                                               # [#]
        freqSimp = 928000 // prec                                               # [#]

        # Populate GFT command ...
        cmd = [
            f"python{sysconfig.get_python_version()}", "-m", "gft",
            "0.0", "0.0", f"{spd:.1f}",
            "--duration", "0.01",
            "--freqLand", f"{freqLand:d}",          # 8 hours land re-evaluation
            "--freqPlot", f"{freqPlot:d}",          # 1 hour plotting
            "--freqSimp", f"{freqSimp:d}",          # 1 hour simplification
            "--GSHHG-resolution", gshhgRes,
            "--nAng", f"{nAng:d}",                  # LOOP VARIABLE
            "--NE-resolution", neRes,               # LOOP VARIABLE
            "--precision", f"{prec:.1f}",           # LOOP VARIABLE
        ]
        if args.debug:
            cmd.append("--debug")

        print(f'Running "{" ".join(cmd)}" ...')

        # Run GFT ...
        if not args.dryRun:
            subprocess.run(
                cmd,
                   check = False,
                encoding = "utf-8",
                  stderr = subprocess.DEVNULL,
                  stdout = subprocess.DEVNULL,
                 timeout = None,
            )

    # **************************************************************************

    # Define axes for initial image ...
    dLon = 10.0                                                                 # [°]
    dLat = 10.0                                                                 # [°]
    nLon = 36                                                                   # [px]
    nLat = 18                                                                   # [px]

    # Define scale for final upscaled image ...
    scale = 100

    # Loop over combinations ...
    for nAng, neRes, prec, color in combs:
        # Deduce directory name ...
        dname = f"res={neRes}_cons=2.00e+00_tol=1.00e-10/local=F_nAng={nAng:d}_prec={prec:.2e}"

        # Deduce file name and skip if it is missing ...
        fname = f"{dname}/allLands.wkb.gz"
        if not os.path.exists(fname):
            continue

        print(f"Surveying \"{fname}\" ...")

        # **********************************************************************

        # Initialize array ...
        histArr = numpy.zeros((nLat, nLon), dtype = numpy.uint64)               # [#]

        # Load [Multi]Polygon ...
        with gzip.open(fname, mode = "rb") as gzObj:
            allLands = shapely.wkb.loads(gzObj.read())

        # Loop over Polygons ...
        for allLand in pyguymer3.geo.extract_polys(allLands, onlyValid = False, repair = False):
            # Loop over coordinates in the exterior ring ...
            for coord in allLand.exterior.coords:
                # Find the pixel that this coordinate corresponds to ...
                iLon = max(0, min(nLon - 1, math.floor((coord[0] + 180.0) / dLon))) # [px]
                iLat = max(0, min(nLat - 1, math.floor(( 90.0 - coord[1]) / dLat))) # [px]

                # Increment array ...
                histArr[iLat, iLon] += 1                                        # [#]

        print(f" > Maximum value = {histArr.max():,d}.")

        # **********************************************************************

        # NOTE: Maximum value = 18.
        # NOTE: Maximum value = 34.
        # NOTE: Maximum value = 66.

        # **********************************************************************

        # Initialize array ...
        histImgArr = numpy.zeros((nLat * scale, nLon * scale, 3), dtype = numpy.uint8)

        # Loop over initial longitudes ...
        for iLon0 in range(nLon):
            # Deduce final upscaled indices ...
            iLon1 =  iLon0      * scale                                         # [px]
            iLon2 = (iLon0 + 1) * scale                                         # [px]

            # Loop over initial latitudes ...
            for iLat0 in range(nLat):
                # Deduce final upscaled indices ...
                iLat1 =  iLat0      * scale                                     # [px]
                iLat2 = (iLat0 + 1) * scale                                     # [px]

                # Populate array ...
                for iLon in range(iLon1, iLon2):
                    for iLat in range(iLat1, iLat2):
                        if histArr[iLat0, iLon0] > 0:
                            color = round(
                                min(
                                    255.0,
                                    255.0 * histArr[iLat0, iLon0].astype(numpy.float64) / 66.0,
                                )
                            )
                            histImgArr[iLat, iLon, :] = cts["turbo"][color][:]
                        else:
                            histImgArr[iLat, iLon, :] = 255

        # Convert array to image ...
        histImgObj = PIL.Image.fromarray(histImgArr)

        # **********************************************************************

        # Create drawing object ...
        histDraw = PIL.ImageDraw.Draw(histImgObj)

        # Loop over Polygons ...
        for allLand in pyguymer3.geo.extract_polys(allLands, onlyValid = False, repair = False):
            # Initialize list ...
            coords = []                                                         # [px], [px]

            # Loop over coordinates in exterior ring ...
            for coord in allLand.exterior.coords:
                # Deduce location and append to list ...
                x = max(0.0, min(float(nLon * scale), float(scale) * (coord[0] + 180.0) / dLon))    # [px]
                y = max(0.0, min(float(nLat * scale), float(scale) * ( 90.0 - coord[1]) / dLat))    # [px]
                coords.append((x, y))                                           # [px], [px]

            # Draw exterior ring ...
            histDraw.line(coords, fill = (255, 255, 255), width = 1)

        # **********************************************************************

        print(f"Saving \"complexity_res={neRes}_cons=2.00e+00_nAng={nAng:d}_prec={prec:.2e}.png\" ...")

        # Save PNG ...
        histImgObj.save(f"complexity_res={neRes}_cons=2.00e+00_nAng={nAng:d}_prec={prec:.2e}.png")
        pyguymer3.image.optimise_image(
            f"complexity_res={neRes}_cons=2.00e+00_nAng={nAng:d}_prec={prec:.2e}.png",
              debug = args.debug,
              strip = True,
            timeout = args.timeout,
        )
