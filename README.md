[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/dannywade/net-textorial)

# net-textorial

## Introduction
Originally developed by [@JulioPDX](https://github.com/JulioPDX), this was a simple app showing off the power of a text-based user interface (TUI) and how it can be used with network automation.

With recent changes, it has evolved into a learning tool that shows network engineers the differences between raw (human-friendly) CLI output and parsed (structured) output. The tool will take any 'show' command and produce the raw and parsed outputs (using [ntc-templates](https://github.com/networktocode/ntc-templates) for parsing). This will be valuable for engineers that want to learn and see the differences between raw (unstructured) and parsed (structured) data outputs.

Under the hood, this tool is leveraging [Netmiko](https://github.com/ktbyers/netmiko) and [Textual](https://textual.textualize.io/). Thank you to all involved!

## Features
- **It just works**: Set your device CLI credentials as environment variables and let it rip! No need to define a device type! All device types are automagically determined using Netmiko's awesome `ssh_autodetect` module.
- **Vendor agnostic**: This tool is not built for a particular vendor. With vendor-agnostic libraries being used under the hood, many different device vendors and device types are supported. See [Device Support](#device-support) section for more details.

## Get Started

```shell
git clone https://github.com/dannywade/net-textual
cd net-textual
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Basic Usage

1. Set your device CLI credentials as environment variables. The variable key names are `NET_TEXT_USER` and `NET_TEXT_PASS`. If device CLI credentials are not set, the default value of *admin* is set for both username and password.

    ```shell
    NET_TEXT_USER=<your username>
    NET_TEXT_PASS=<your password>
    ```
2. Run the app

    ```shell
    python net.py
    ```
3. Enter the hostname/IP of the device and a valid 'show' command in the input box

    ```shell
    dist-router1 show ip route
    ```

## Supported Devices/Parsers

### Device Support

Any device that is supported by Netmiko can be used with this tool. Under the hood, all device connections are created using the Netmiko library. Here are some of the popular supported (and tested) platforms by Netmiko:
- Arista vEOS
- Cisco ASA, IOS, IOS-XE, IOS-XR, NX-OS
- HP ProCurve
- Juniper Junos
- Linux


### Parser Support

With Genie and ntc-templates (TextFSM) being the two major parsing libraries in the game, there's a goal to support both libraries. Currently, only ntc-templates is supported and used to parse all command output. Genie parsers will be supported in the future.

## Demo


https://user-images.githubusercontent.com/13680237/199552401-9e9c58b0-6cd9-4dcb-8512-b91cc8d010b0.mov

