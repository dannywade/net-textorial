# net-textual

Originally developed by [@JulioPDX](https://github.com/JulioPDX), this is a simple app showing off the power of a text user interface (TUI) and how it can be used with network automation.

With recent changes, it has evolved into a learning tool that shows network engineers the differences between raw (human-friendly) CLI output and parsed (structured) output. The tool will take any 'show' command and produce the raw and parsed outputs (using [ntc-templates](https://github.com/networktocode/ntc-templates)). This will be valuable for engineers that want to learn or visualize the differences between the two outputs.

Under the hood, this is leveraging [Netmiko](https://github.com/ktbyers/netmiko) and [Textual](https://textual.textualize.io/). Thank you to all involved!

## Get Started

```shell
git clone https://github.com/dannywade/net-textual
cd net-textual
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Basic Usage

1. Update device credentials in the app code
2. Run the app
    ```shell
    python net.py
    ```
3. Enter the hostname/IP of the device and a valid 'show' command in the input box
    ```shell
    dist-router1 show ip route
    ```

## Caveats

- The app currently has hardcoded device credentials in `net.py` for the Cisco DevNet Always-On sandbox that's running a Cisco CSR on a recommended code version. I highly recommend altering the code to use environment variables or a vault solution instead of hardcoding your device credentials. There will be changes to the app code in the future, but for now it's still in a prototype phase.

## Demo


https://user-images.githubusercontent.com/13680237/199552401-9e9c58b0-6cd9-4dcb-8512-b91cc8d010b0.mov

