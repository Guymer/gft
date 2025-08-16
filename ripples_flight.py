#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import glob
    import gzip
    import os
    import pathlib
    import platform
    import shutil
    import subprocess
    import sysconfig

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
        import matplotlib
        matplotlib.rcParams.update(
            {
                       "backend" : "Agg",                                       # NOTE: See https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html
                    "figure.dpi" : 300,
                "figure.figsize" : (9.6, 7.2),                                  # NOTE: See https://github.com/Guymer/misc/blob/main/README.md#matplotlib-figure-sizes
                     "font.size" : 8,
            }
        )
        import matplotlib.pyplot
    except:
        raise Exception("\"matplotlib\" is not installed; run \"pip install --user matplotlib\"") from None
    try:
        import shapely
        import shapely.geometry
        import shapely.wkb
    except:
        raise Exception("\"shapely\" is not installed; run \"pip install --user Shapely\"") from None

    # Import my modules ...
    try:
        import pyguymer3
        import pyguymer3.geo
        import pyguymer3.image
        import pyguymer3.media
    except:
        raise Exception("\"pyguymer3\" is not installed; run \"pip install --user PyGuymer3\"") from None

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "Show the ripples spreading.",
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
        "--ffmpeg-path",
        default = shutil.which("ffmpeg7") if platform.system() == "Darwin" else shutil.which("ffmpeg"),
           dest = "ffmpegPath",
           help = "the path to the \"ffmpeg\" binary",
           type = str,
    )
    parser.add_argument(
        "--ffprobe-path",
        default = shutil.which("ffprobe7") if platform.system() == "Darwin" else shutil.which("ffprobe"),
           dest = "ffprobePath",
           help = "the path to the \"ffprobe\" binary",
           type = str,
    )
    parser.add_argument(
        "--plot",
        action = "store_true",
          help = "make maps and animation",
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

    # Define starting location (Tokyo Haneda) ...
    lon = 139.779999                                                            # [°]
    lat =  35.552299                                                            # [°]

    # Define finishing location (Helsinki Vantaa)
    finishLon = 24.963341                                                       # [°]
    finishLat = 60.318363                                                       # [°]

    # Find the middle of great circle (which would be the ideal flight plan) ...
    midLon, midLat = pyguymer3.geo.find_middle_of_great_circle(
        lon,
        lat,
        finishLon,
        finishLat,
    )                                                                           # [°], [°]

    # Find the great circle (which would be the ideal flight plan) ...
    greatCircle = pyguymer3.geo.great_circle(
            lon,
            lat,
            finishLon,
            finishLat,
          debug = args.debug,
        maxdist = 10.0e3,
    )

    # Define combinations ...
    combs = [
        ( 9, "110m", 116000     , (1.0, 0.0, 0.0, 1.0),),
        (17,  "50m", 116000 // 2, (0.0, 1.0, 0.0, 1.0),),
        (33,  "10m", 116000 // 4, (0.0, 0.0, 1.0, 1.0),),
    ]
    spd = 500.0                                                                 # [kts]

    # Determine output directory and make it if it is missing ...
    outDir = "_".join(
        [
            "nAng=" + ",".join([f"{nAng:d}" for nAng, neRes, prec, color in combs]),
            "neRes=" + ",".join([neRes for nAng, neRes, prec, color in combs]),
            "prec=" + ",".join([f"{prec:.2e}" for nAng, neRes, prec, color in combs]),
        ]
    )
    if not os.path.exists(outDir):
        os.mkdir(outDir)
    if not os.path.exists(f"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}"):
        os.mkdir(f"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}")

    # **************************************************************************

    # Create the initial starting Point ...
    plane = shapely.geometry.point.Point(lon, lat)

    # **************************************************************************

    # Loop over hours ...
    for dur in range(1, 25):
        # Loop over combinations ...
        for nAng, neRes, prec, color in combs:
            # Create short-hands ...
            # NOTE: Say that 928,000 metres takes 1 hour at 500 knots.
            freqLand = 8 * 928000 // prec                                       # [#]
            freqPlot = 928000 // prec                                           # [#]
            freqSimp = 928000 // prec                                           # [#]

            # Populate GFT command ...
            cmd = [
                f"python{sysconfig.get_python_version()}", "-m", "gft",
                f"{lon:+.6f}", f"{lat:+.6f}", f"{spd:.1f}",
                "--duration", f"{dur / 24.0:.2f}",  # LOOP VARIABLE
                "--freqLand", f"{freqLand:d}",      # 8 hours land re-evaluation
                "--freqPlot", f"{freqPlot:d}",      # 1 hour plotting
                "--freqSimp", f"{freqSimp:d}",      # 1 hour simplification
                "--GSHHG-resolution", gshhgRes,
                "--nAng", f"{nAng:d}",              # LOOP VARIABLE
                "--NE-resolution", neRes,           # LOOP VARIABLE
                "--precision", f"{prec:.1f}",       # LOOP VARIABLE
            ]
            if args.debug:
                cmd.append("--debug")
            if args.plot:
                cmd.append("--plot")

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

    # Loop over combinations ...
    for nAng, neRes, prec, color in combs:
        # Create short-hands ...
        # NOTE: Say that 928,000 metres takes 1 hour at 500 knots.
        freqLand = 8 * 928000 // prec                                           # [#]
        freqPlot = 928000 // prec                                               # [#]
        freqSimp = 928000 // prec                                               # [#]

        # Deduce directory name ...
        dname = f"res={neRes}_cons=2.00e+00_tol=1.00e-10/local=F_nAng={nAng:d}_prec={prec:.2e}/freqLand={freqLand:d}_freqSimp={freqSimp:d}_lon={lon:+011.6f}_lat={lat:+010.6f}/limit"

        # Find the maximum distance that has been calculated so far ...
        fname = sorted(glob.glob(f"{dname}/istep=??????.wkb.gz"))[-1]
        istep = int(os.path.basename(fname).split("=")[1].split(".")[0])        # [#]

        # Create short-hands ...
        maxDist = float(istep * prec)                                           # [m]
        maxDur = maxDist / (1852.0 * spd)                                       # [hr]

        print(f" > {0.001 * maxDist:,.2f} kilometres of flying is available (which is {maxDur:,.4f} hours).")

    # **************************************************************************
    # **************************************************************************
    # **************************************************************************

    # Re-define resolution now that the data has been made ...
    gshhgRes = "l"

    # **************************************************************************
    # **************************************************************************
    # **************************************************************************

    # Initialize list ...
    frames = []

    # Loop over distances ...
    for dist in range(1, 30000 + 1, 1):
        # Deduce PNG name, if it exists then append it to the list and skip ...
        frame = f"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}/dist={dist:05d}_Flight.png"
        if os.path.exists(frame):
            frames.append(frame)
            continue

        # **********************************************************************

        # Initialize list ...
        fnames = []

        # Loop over combinations ...
        for nAng, neRes, prec, color in combs:
            # Skip if this distance cannot exist (because the precision is too
            # coarse) and determine the step count ...
            if (1000 * dist) % prec != 0:
                continue
            istep = ((1000 * dist) // prec) - 1                                 # [#]

            # Create short-hands ...
            # NOTE: Say that 928,000 metres takes 1 hour at 500 knots.
            freqLand = 8 * 928000 // prec                                       # [#]
            freqPlot = 928000 // prec                                           # [#]
            freqSimp = 928000 // prec                                           # [#]

            # Deduce directory name ...
            dname = f"res={neRes}_cons=2.00e+00_tol=1.00e-10/local=F_nAng={nAng:d}_prec={prec:.2e}/freqLand={freqLand:d}_freqSimp={freqSimp:d}_lon={lon:+011.6f}_lat={lat:+010.6f}/limit"

            # Deduce file name and skip if it is missing ...
            fname = f"{dname}/istep={istep + 1:06d}.wkb.gz"
            if not os.path.exists(fname):
                continue

            # Append it to the list ...
            fnames.append(fname)

        # Skip this frame if there are not enough files ...
        if len(fnames) != len(combs):
            continue

        # **********************************************************************

        print(f"Making \"{frame}\" ...")

        # Create figure ...
        fg = matplotlib.pyplot.figure(figsize = (7.2, 7.2))

        # Create axis ...
        # NOTE: Really, I should be plotting "allLands" to be consistent with
        #       the planes, however, as each plane (potentially) is using
        #       different collections of land then I will just use the raw GSHHG
        #       dataset instead.
        ax = pyguymer3.geo.add_axis(
            fg,
            coastlines_resolution = gshhgRes,
                            debug = args.debug,
                              lat = midLat,
                              lon = midLon,
        )

        # Configure axis ...
        pyguymer3.geo.add_map_background(
            ax,
                 debug = args.debug,
                  name = "shaded-relief",
            resolution = "large8192px",
        )

        # Load [Multi]Polygon ...
        with gzip.open(f"{os.path.dirname(os.path.dirname(os.path.dirname(fnames[-1])))}/allLands.wkb.gz", mode = "rb") as gzObj:
            allLands = shapely.wkb.loads(gzObj.read())

        # Plot [Multi]Polygon ...
        # NOTE: Given how "allLands" was made, we know that there aren't any
        #       invalid Polygons, so don't bother checking for them.
        ax.add_geometries(
            pyguymer3.geo.extract_polys(allLands, onlyValid = False, repair = False),
            cartopy.crs.PlateCarree(),
                alpha = 0.5,
            edgecolor = "none",
            facecolor = "magenta",
            linewidth = 0.0,
        )

        # Initialize lists ...
        labels = []
        lines = []

        # Loop over combinations/files ...
        for (nAng, neRes, prec, color), fname in zip(combs, fnames, strict = True):
            print(f" > Loading \"{fname}\" ...")

            # Load [Multi]LineString ...
            with gzip.open(fname, mode = "rb") as gzObj:
                limit = shapely.wkb.loads(gzObj.read())

            # Plot [Multi]LineString ...
            # NOTE: Given how "limit" was made, we know that there aren't any
            #       invalid LineStrings, so don't bother checking for them.
            ax.add_geometries(
                pyguymer3.geo.extract_lines(limit, onlyValid = False),
                cartopy.crs.PlateCarree(),
                edgecolor = color,
                facecolor = "none",
                linewidth = 1.0,
            )

            # Add an entry to the legend ...
            labels.append(f"nAng={nAng:d}, res={neRes}, prec={prec:d}")
            lines.append(matplotlib.lines.Line2D([], [], color = color))

        # Check that the distance isn't too large ...
        if 1000.0 * float(dist) <= pyguymer3.MAXIMUM_VINCENTY:
            # Calculate the maximum distance the plane could have got to ...
            maxPlane = pyguymer3.geo.buffer(
                plane,
                1000.0 * float(dist),
                debug = args.debug,
                 fill = +1.0,
                 nAng = 361,
                 simp = -1.0,
            )

            # Plot [Multi]Polygon ...
            ax.add_geometries(
                pyguymer3.geo.extract_polys(maxPlane, onlyValid = False, repair = False),
                cartopy.crs.PlateCarree(),
                edgecolor = "gold",
                facecolor = "none",
                linewidth = 1.0,
            )

        # Plot the starting and finishing locations ...
        # NOTE: As of 5/Dec/2023, the default "zorder" of the coastlines is 1.5,
        #       the default "zorder" of the gridlines is 2.0 and the default
        #       "zorder" of the scattered points is 1.0.
        ax.scatter(
            [lon, finishLon],
            [lat, finishLat],
                color = "gold",
               marker = "*",
            transform = cartopy.crs.Geodetic(),
               zorder = 5.0,
        )

        # Plot great circle ...
        ax.add_geometries(
            pyguymer3.geo.extract_lines(greatCircle, onlyValid = False),
            cartopy.crs.PlateCarree(),
            edgecolor = "gold",
            facecolor = "none",
            linestyle = "dashed",
            linewidth = 1.0,
        )

        # Create short-hand ...
        dur = 1000.0 * float(dist) / (1852.0 * spd)                             # [hr]

        # Configure axis ...
        ax.legend(
            lines,
            labels,
            loc = "lower left",
        )
        ax.set_title(
            f"{dist:6,d} km ({dur:5.2f} hours)",
            fontfamily = "monospace",
                   loc = "right",
        )

        # Configure figure ...
        fg.tight_layout()

        # Save figure ...
        fg.savefig(frame)
        matplotlib.pyplot.close(fg)

        # Optimize PNG ...
        pyguymer3.image.optimise_image(
            frame,
              debug = args.debug,
              strip = True,
            timeout = args.timeout,
        )

        # Append frame to list ...
        frames.append(frame)

    # **************************************************************************

    print(f"Making \"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}_Flight.mp4\" ...")

    # Save 25 fps MP4 ...
    vname = pyguymer3.media.images2mp4(
        frames,
              debug = args.debug,
        ffprobePath = args.ffprobePath,
         ffmpegPath = args.ffmpegPath,
            timeout = args.timeout,
    )
    shutil.move(vname, f"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}_Flight.mp4")

    # Set maximum sizes ...
    # NOTE: By inspection, the PNG frames are 2,160 px tall/wide.
    maxSizes = [512, 1024, 2048]                                                # [px]

    # Loop over maximum sizes ...
    for maxSize in maxSizes:
        print(f"Making \"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}_Flight{maxSize:04d}px.mp4\" ...")

        # Save 25 fps MP4 ...
        vname = pyguymer3.media.images2mp4(
            frames,
                   debug = args.debug,
             ffprobePath = args.ffprobePath,
              ffmpegPath = args.ffmpegPath,
            screenHeight = maxSize,
             screenWidth = maxSize,
                 timeout = args.timeout,
        )
        shutil.move(vname, f"{outDir}/lon={lon:+011.6f}_lat={lat:+010.6f}_Flight{maxSize:04d}px.mp4")
