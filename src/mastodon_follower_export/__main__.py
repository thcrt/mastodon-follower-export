# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("instance", help="The Mastodon instance on which your account is hosted.")
    parser.add_argument("username", help="Your username.")
    parser.parse_args()

if __name__ == "__main__":
    main()
