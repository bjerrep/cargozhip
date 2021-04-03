#!/usr/bin/env python3
import cz


def test_exclude_file_hit():
    assert not cz.exclude_file_hit('inc/test.h', ['test'])
    assert not cz.exclude_file_hit('inc/test.h', ['inc'])


def test_exclude_dir_hit():
    assert not cz.exclude_dir_hit('inc/test.h', ['test'])
    assert cz.exclude_dir_hit('inc/test.h', ['inc'])


test_exclude_file_hit()
test_exclude_dir_hit()

print('\n---------------')
print(' Tests passed')
print('---------------\n')
