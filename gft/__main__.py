#!/usr/bin/env python3

# Use the proper idiom in the main module ...
# NOTE: See https://docs.python.org/3.12/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    # Import standard modules ...
    import argparse
    import platform
    import shutil

    # Import sub-functions ...
    from .fly import fly

    # **************************************************************************

    # Create argument parser and parse the arguments ...
    parser = argparse.ArgumentParser(
           allow_abbrev = False,
            description = "This wrapper reads in a starting coordinate and a flying speed and then calculates the maximum possible flying distance above the surface of the Earth that the plane can reach in the specified time avoiding user-provided countries.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "lon",
        help = "the longitude of the starting point (in degrees)",
        type = float,
    )
    parser.add_argument(
        "lat",
        help = "the latitude of the starting point (in degrees)",
        type = float,
    )
    parser.add_argument(
        "spd",
        help = "the speed of the plane (in knots)",
        type = float,
    )
    parser.add_argument(
        "--avoid-countries",
        default = [
            "Baikonur",
            "Belarus",
            "Iran",
            "Russia",
            "Ukraine",
        ],
           dest = "avoidCountries",
           help = "the countries to be avoided",
          nargs = "+",
           type = str,
    )
    parser.add_argument(
        "--conservatism",
        default = 2.0,
           dest = "cons",
           help = "the amount of conservatism to add to the calculation",
           type = float,
    )
    parser.add_argument(
        "--debug",
        action = "store_true",
          help = "print debug messages",
    )
    parser.add_argument(
        "--duration",
        default = 1.0,
           dest = "dur",
           help = "the duration of the voyage (in days)",
           type = float,
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
        "--freqLand",
        default = 100,
           help = "re-evaluate the relevant land every freqLand iteration",
           type = int,
    )
    parser.add_argument(
        "--freqPlot",
        default = 25,
           help = "plot flying contours every freqPlot iteration",
           type = int,
    )
    parser.add_argument(
        "--freqSimp",
        default = 25,
           help = "simplify the flying contour every freqSimp iteration",
           type = int,
    )
    parser.add_argument(
        "--GSHHG-resolution",
        default = "c",
           dest = "gshhgRes",
           help = "the resolution of the Global Self-Consistent Hierarchical High-Resolution Geography datasets",
           type = str,
    )
    parser.add_argument(
        "--local",
        action = "store_true",
          help = "the plot has only local extent",
    )
    parser.add_argument(
        "--nAng",
        default = 9,
           help = "the number of directions from each point that the plane could fly in",
           type = int,
    )
    parser.add_argument(
        "--NE-resolution",
        default = "110m",
           dest = "neRes",
           help = "the resolution of the Natural Earth datasets",
           type = str,
    )
    parser.add_argument(
        "--nIter",
        default = 1000000,
           dest = "nIter",
           help = "the maximum number of iterations (particularly the Vincenty formula)",
           type = int,
    )
    parser.add_argument(
        "--plot",
        action = "store_true",
          help = "make maps and animation",
    )
    parser.add_argument(
        "--precision",
        default = 10000.0,
           dest = "prec",
           help = "the precision of the calculation (in metres)",
           type = float,
    )
    parser.add_argument(
        "--timeout",
        default = 60.0,
           help = "the timeout for any requests/subprocess calls (in seconds)",
           type = float,
    )
    parser.add_argument(
        "--tolerance",
        default = 1.0e-10,
           dest = "tol",
           help = "the Euclidean distance that defines two points as being the same (in degrees)",
           type = float,
    )
    args = parser.parse_args()

    # Check that "ffmpeg" and "ffprobe" are installed ...
    assert args.ffmpegPath is not None, "\"ffmpeg\" is not installed"
    assert args.ffprobePath is not None, "\"ffprobe\" is not installed"

    # **************************************************************************

    # Sail the plane ...
    fly(
        args.lon,
        args.lat,
        args.spd,
        avoidCountries = args.avoidCountries,
                  cons = args.cons,
                 debug = args.debug,
                   dur = args.dur,
            ffmpegPath = args.ffmpegPath,
           ffprobePath = args.ffprobePath,
              freqLand = args.freqLand,
              freqPlot = args.freqPlot,
              freqSimp = args.freqSimp,
              gshhgRes = args.gshhgRes,
                 local = args.local,
                  nAng = args.nAng,
                 neRes = args.neRes,
                 nIter = args.nIter,
                  plot = args.plot,
                  prec = args.prec,
               timeout = args.timeout,
                   tol = args.tol,
    )
