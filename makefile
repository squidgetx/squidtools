default: update-local

update-local:
	python setup.py bdist_wheel
	pip install --force-reinstall dist/squidtools*.whl
