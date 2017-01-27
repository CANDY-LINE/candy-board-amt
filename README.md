# candy-board-amt

[![GitHub release](https://img.shields.io/github/release/CANDY-LINE/candy-board-amt.svg)](https://github.com/CANDY-LINE/candy-board-amt/releases/latest)
[![Build Status](https://travis-ci.org/CANDY-LINE/candy-board-amt.svg?branch=master)](https://travis-ci.org/CANDY-LINE/candy-board-amt)
[![License BSD3](https://img.shields.io/github/license/CANDY-LINE/candy-board-amt.svg)](http://opensource.org/licenses/BSD-3-Clause)

Base CANDY LINE boards service for AM Telecom Modules

## pip Installation

```
$ pip install candy-board-amt
```

## pip Uninstallation

```
$ pip candy-board-amt
```

## Development

### Prerequisites

 * [pandoc](http://pandoc.org)
 * [pypandoc](https://pypi.python.org/pypi/pypandoc/1.2.0)

On Mac OS:

```
$ brew install pandoc
$ pip install pypandoc
```

### Local Installation test

```
$ ./setup.py install --record files.txt
```

### Local Uninstallation test

```
$ cat files.txt | xargs rm -rf
```

## Test

```
$ ./setup.py test
```

# Revision history
* 1.2.1
    - Handle uncaught exception
    - Suppress useless log

* 1.2.0
    - Improve serial port resolver function
    - Add a new feature to ensure the opened port is online on creating a new serial port object

* 1.1.1
    - Fix an issue where the running thread stops on exception thrown

* 1.1.0
    - Add a new modem command to enable auto-connect mode

* 1.0.1
    - Fix an issue where echo back line can be included into the result string
    - Fix an issue where CI test was failure because of unnecessary dependency on pypandoc

* 1.0.0
    - Initial public release

* 0.1.1-0.1.3
    - Fix resolve_modem_port()

* 0.1.0
    - Remove modem_auto_connect()
    - Add a new function to enable ACM, modem_enable_acm()
    - Add a new function delete APN, apn_del()
    - Add a new static function to resolve modem serial port

* 0.0.1
    - Initial beta release
