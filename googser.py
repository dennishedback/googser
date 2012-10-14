#! /usr/bin/python

import sys
import getopt
import urllib.request
import urllib.parse
import urllib.error
import html.parser
import time
import random


class Configuration:
    def __init__(self, num_pages, force, output_file, lang):
        self.num_pages = num_pages
        self.force = force
        self.output_file = output_file
        self.lang = lang


class SearchError(Exception):
    def __init__(self, strerror):
        self.strerror = strerror


class OptArgError(Exception):
    def __init__(self, strerror):
        self.strerror = strerror


class GoogserHTMLParser(html.parser.HTMLParser):
    search_results = []
    _in_r = False

    def reset_results(self):
        self.search_results = []

    def _handle_link_attr(self, attr, val):
        if attr == "href" and self._in_r:
            self.search_results.append(val)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, val in attrs:
                self._handle_link_attr(attr, val)
        if tag == "h3":
            for attr, val in attrs:
                if attr == "class" and val == "r":
                    self._in_r = True

    def handle_endtag(self, tag):
        if tag == "h3":
            self._in_r = False


def print_usage():
    print("Usage: googser [OPTION]... [SEARCH TERM]")
    print("Retrieves Google results for SEARCH TERM"
          " to file or standard output.")
    print()
    print("  -f, --force      no human behaviour, faster -- use at own risk")
    print("  -l, --lang=L     search language, default is 'en'")
    print("  -n, --number=N   number"
          " of pages to fetch instead of default number (1)")
    print("  -o, --output=F   appends results to file,"
          " creates file if it doesn't exist")
    print("      --help       display this help and exit")
    print("      --version    output version information and exit")


def print_version():
    print("googser 0.9.0")
    print("Copyright (C) 2012 Dennis Hedback")


def print_usage_reference():
    print("Try 'googser --help' for more information.", file=sys.stderr)


def request_html(uri, user_agent):
    req = urllib.request.Request(uri, headers={"User-Agent": user_agent})
    f = urllib.request.urlopen(req)
    html = f.read().decode("utf-8")
    return html


def mimic_human():
    random.seed()
    sleep_seconds = random.randrange(15, 40)
    time.sleep(sleep_seconds)


def search(search_term, conf):
    user_agent = ("Mozilla/5.0 (Windows NT 6.1; rv:10.0) "
                  "Gecko/20100101 Firefox/10.0")
    base_uri = ("https://www.google.com/search?hl=" + conf.lang  + "&q=" +
                urllib.parse.quote(search_term).replace("%20", "+"))
    results = []
    try:
        parser = GoogserHTMLParser(strict=False)
        for i in range(0, conf.num_pages):
            uri = base_uri
            if i > 0:
                uri += "&start=" + str(i * 10)
            html = request_html(uri, user_agent)
            parser.feed(html)
            results.extend(parser.search_results)
            parser.reset_results()
            if ((not conf.force)
                    and (conf.num_pages > 1)
                    and (i != conf.num_pages - 1)):
                mimic_human()
    except urllib.error.URLError as err:
        raise SearchError(err.reason)
    except html.parser.HTMLParseError as err:
        raise SearchError(err.msg)
    return results


def print_results(results, file):
    for uri in results:
        file.write(uri + "\n")


def parse_opts_args(argv, conf):
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "n:fo:l:",
            ["number=", "force", "output=", "lang=", "help", "version"]
        )
    except getopt.GetoptError as err:
        raise OptArgError(str(err))
    for opt, arg in opts:
        if opt == "--help":
            print_usage()
            sys.exit(0)
        elif opt == "--version":
            print_version()
            sys.exit(0)
        elif opt in ("-n", "--number"):
            if int(arg) > 1:
                conf.num_pages = int(arg)
        elif opt in ("-f", "--force"):
            conf.force = True
        elif opt in ("-o", "--output"):
            conf.output_file = arg
        elif opt in ("-l", "--lang"):
            conf.lang = arg
    if len(args) == 0:
        raise OptArgError("No search term provided")
    return args


def main(argv):
    try:
        conf = Configuration(1, False, None, "en")
        args = parse_opts_args(argv, conf)
        results = search(" ".join(args), conf)
        if conf.output_file is None:
            print_results(results, sys.stdout)
        else:
            with open(conf.output_file, "w") as f:
                print_results(results, f)
    except OptArgError as err:
        print(err.strerror, file=sys.stderr)
        print_usage_reference()
        return 2
    except (SearchError, IOError) as err:
        print(err.strerror, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
