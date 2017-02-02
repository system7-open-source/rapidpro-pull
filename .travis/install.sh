#!/usr/bin/env bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]
then
	export PATH="~/.pyenv/bin:$PATH"
	eval "$(pyenv init -)"
	eval "$(pyenv virtualenv-init -)"
	pyenv versions
	pyenv install pypy-5.6.0
	pyenv global system pypy-5.6.0
	pyenv versions
fi
which python
which pypy
pip install -U pip
pip install tox tox-travis
which tox
pip install -e .[development]
