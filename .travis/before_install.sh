#!/usr/bin/env bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]
then
	brew update >/dev/null || brew update >/dev/null
	brew outdated pyenv || brew upgrade pyenv
fi
