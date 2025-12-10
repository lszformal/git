#!/bin/sh
#
# Copyright (c) 2024 Git Contributors
#

test_description='basic coverage for git version'

. ./test-lib.sh

test_expect_success '--short outputs only the version string' '
	git version --short >actual &&
	git version | sed "s/^git version //" >expect &&
	test_cmp expect actual
'

test_expect_success '--short can be combined with --build-options' '
	git version --short --build-options >actual &&
	head -n1 actual >actual.version &&
	tail -n +2 actual >actual.options &&
	git version --build-options >expect &&
	sed -n "1p" expect | sed "s/^git version //" >expect.version &&
	tail -n +2 expect >expect.options &&
	test_cmp expect.version actual.version &&
	test_cmp expect.options actual.options
'

test_done
