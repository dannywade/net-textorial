# net-textual

Originally developed by [@JulioPDX](https://github.com/JulioPDX), this is a simple app showing off the power of a text user interface (TUI) and how it can be used with network automation.

With recent changes, it has evolved into a learning tool that shows network engineers the differences between raw (human-friendly) CLI output and parsed (structured) output. The tool will take any 'show' command and produce the raw and parsed outputs (using [ntc-templates](https://github.com/networktocode/ntc-templates)). This will be valuable for engineers that want to learn or visualize the differences between the two outputs.

Under the hood, this is leveraging [Netmiko](https://github.com/ktbyers/netmiko) and [Textual](https://textual.textualize.io/). Thank you to all involved!

## Get started

```shell
git clone https://github.com/dannywade/net-textual
cd net-textual
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Start the app and have fun

```shell
python3 net.py
```

## Demo


https://user-images.githubusercontent.com/13680237/199552401-9e9c58b0-6cd9-4dcb-8512-b91cc8d010b0.mov

