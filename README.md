# candy-board-amt

[![GitHub release](https://img.shields.io/github/release/CANDY-LINE/candy-board-amt.svg)](https://github.com/CANDY-LINE/candy-board-amt/releases/latest)
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

## Local Installation test

```
$ ./setup.py install --record files.txt
```

## Local Uninstallation test

```
$ cat files.txt | xargs rm -rf
```

# Revision history
 * 0.1.0
   - Remove modem_auto_connect()
   - Add a new function to enable ACM, modem_enable_acm()
   - Add a new function delete APN, apn_del()
   - Add a new static function to resolve modem serial port

 * 0.0.1
    - Initial beta release
