# !/bin/bash
#
# Copyright (c) 2020 The UESTC-Signin Authors. All rights reserved.
# Use of this source code is governed by a MIT-style license that can be
# found in the LICENSE file. See the AUTHORS file for names of contributors.
#
# Authors: ehds(ds.he@foxmail.com)

rm -rf driver data logs
mkdir driver data logs

echo "Installing geckodriver"
pushd driver
# linux
# curl -fSL https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz -o geckodriver.tar.gz
# tar -zxvf geckodriver.tar.gz
# rm -rf *.gz
# windws
curl -fSL https://github.com/mozilla/geckodriver/releases/download/v0.29.0/geckodriver-v0.29.0-win64.zip -o geckodriver.zip
unzip geckodriver.zip
rm -rf *.zip

popd

pip3 install -r requirments.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
echo "Successfuly installed"
