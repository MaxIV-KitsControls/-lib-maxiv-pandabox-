import json
import argparse
try:
    from ._version import version as scm_version
except ImportError:
    scm_version = "0.0+unknown"


# ----------------------------------------------------------
def version():
    """
    Current version.
    """
    return scm_version


# ----------------------------------------------------------
def meta(given_meta=None):
    """
    Returns version information as a dict.
    Adds version information to given meta, if any.
    """
    s = {}
    s["lib_maxiv_pandabox"] = version()

    if given_meta is not None:
        given_meta.update(s)
    else:
        given_meta = s
    return given_meta


# ----------------------------------------------------------
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print version stack in json.",
    )

    # -------------------------------------------------------------------------
    given_args, remaining_args = parser.parse_known_args()

    if given_args.json:
        print(json.dumps(meta(), indent=4))
    else:
        print(version())


# ----------------------------------------------------------
if __name__ == "__main__":
    main()
