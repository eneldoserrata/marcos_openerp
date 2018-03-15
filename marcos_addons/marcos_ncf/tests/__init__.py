# -*- encoding: utf-8 -*-
"""
Tests for marcos_ncf module.

This module groups a few sub-modules containing unittest2 test cases.

Tests can be explicitely added to the `fast_suite` or `checks` lists or not.
See the :ref:`test-framework` section in the :ref:`features` list.

To run tests:
$ ./openerp-server -c .openerp_serverrc -d db -u module --log-level=test --test-enable

"""

# import test_ir_sequence
import test_purchase_order

# When updated
fast_suite = [
    test_purchase_order,
]

# When installed
checks = [
]
