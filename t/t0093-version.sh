#!/bin/sh

test_description='git version options'

. ./test-lib.sh

strip_prefix() {
	sed -e 's/^git version //'
}

test_expect_success 'git version --short omits prefix' '
	git version --short >actual &&
	git version | strip_prefix >expect &&
	test_cmp expect actual
'

test_expect_success 'git version --short rejects build options' '
	test_must_fail git version --short --build-options 2>err &&
	grep "option \`--short\` cannot" err
'

test_expect_success 'git version keeps prefix when not shortened' '
	git version >actual &&
	git version --short >short &&
	sed "s/^/git version /" short >expect &&
	test_cmp expect actual
'

test_done
