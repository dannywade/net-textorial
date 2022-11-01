# net-textual

Simple app showing the use-case of text user interface (TUI) with network devices.

Under the hood, this is leveraging two excellent projects in [NAPALM](https://napalm.readthedocs.io/en/latest/) and [Textual](https://textual.textualize.io/). Thank you to all involved!

## Get started

```shell
git clone https://github.com/JulioPDX/net-textual.git
cd net-textual
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Lab

This repo leverages a simple [Containerlab](https://containerlab.dev/) file to deploy two Arista EOS nodes. Check out their documentation to get started.

```shell
sudo containerlab deploy -t clab.yml
```

## Start the app and have fun

```shell
python3 net.py
```

Example of the app running below!

[![asciicast](https://asciinema.org/a/533872.svg)](https://asciinema.org/a/533872)
