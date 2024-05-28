rm -rf dist/*
python3 setup.py sdist build
twine upload --repository feishuconnector dist/feishuconnector-0.1.*.tar.gz
