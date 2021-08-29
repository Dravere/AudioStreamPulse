#!/bin/python3

import datetime
import json
import os
import sys
import subprocess

# load-module module-null-sink sink_name=MIXER_NAME sink_properties=device.description=MIXER_NAME
# load-module module-loopback source=<Select Monitor> latency_msec=10 sink=MIXER_NAME
# load-module module-loopback source=<Select Microphone> latency_msec=10 sink=MIXER_NAME
# load-module module-remap-source source_name=AllAudio master=MIXER_NAME.monitor

# Storage location for config file
CONFIG_FILE = '~/.config/AudioStreamPulse/config.json'

# Storage location for module ids to be used with stop. Recommended to be in /tmp, so it is deleted upon restart.
SETUP_CONFIG_FILE = '/tmp/audiostreampulse.json'
SETUP_CONFIG_FILE_VERSION = 1

# Name of the sink in which the audio and microphone is mixed. No spaces allowed!
MIXER_NAME = 'MixingInputOutput'


def pactl_list(module_type):
    result = subprocess.run(['pactl', 'list', 'short', module_type], capture_output=True, encoding='utf-8', text=True)
    if result.returncode != 0:
        exit(-1)

    lines = result.stdout.split('\n')
    data = []
    for line in lines:
        line = line.strip()
        if line == '':
            continue
        columns = line.split('\t')
        data.append({
            'id': columns[0],
            'name': columns[1]
        })

    return data


def pactl_load_module(module, parameters):
    cmd = ['pactl', 'load-module', module]
    cmd.extend(parameters)
    result = subprocess.run(cmd, capture_output=True, encoding='utf-8', text=True)
    if result.returncode != 0:
        return None

    return result.stdout.strip()


def pactl_unload_module(identifier):
    subprocess.run(['pactl', 'unload-module', identifier])


def select_module(title, modules, default_index=None):
    print(title)
    for i, module in enumerate(modules):
        print(i, module['name'])

    default_text = '' if default_index is None else ' (default: ' + modules[default_index]['name'] + ')'
    selection = input('Selection' + default_text + ': ')

    try:
        index = int(selection)
        if 0 <= index < len(modules):
            return modules[index]
        return None
    except ValueError:
        if default_index is not None:
            return modules[default_index]
        return None


def find_module(modules, module_name):
    for i, module in enumerate(modules):
        if module['name'] == module_name:
            return i

    return None


def write_config(config):
    with open(CONFIG_FILE, 'wt', encoding='utf-8') as file:
        json.dump(config, file)


def read_config():
    try:
        with open(CONFIG_FILE, 'rt', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'microphone': '', 'output_monitor': ''}


def start():
    config = read_config()
    sources = pactl_list('sources')
    microphone = select_module('Select the default microphone', sources, find_module(sources, config['microphone']))
    if microphone is None:
        print('No valid microphone selected!')
        exit(-1)

    print()
    output_monitor = select_module('Select the audio monitor', sources, find_module(sources, config['output_monitor']))
    if output_monitor is None:
        print('No valid monitor selected!')
        exit(-1)

    mixer = pactl_load_module(
        'module-null-sink',
        ['sink_name=' + MIXER_NAME, 'sink_properties=device.description=' + MIXER_NAME])

    mixer_input_default_output = pactl_load_module(
        'module-loopback',
        ['source=' + output_monitor['name'], 'latency_msec=10', 'sink=' + MIXER_NAME])

    mixer_input_microphone = pactl_load_module(
        'module-loopback',
        ['source=' + microphone['name'], 'latency_msec=10', 'sink=' + MIXER_NAME])

    virtual_microphone = pactl_load_module(
        'module-remap-source',
        ['source_name=AllAudio', 'master=' + MIXER_NAME + '.monitor'])

    with open(SETUP_CONFIG_FILE, 'wt', encoding='utf-8') as f:
        json.dump({
            'version': SETUP_CONFIG_FILE_VERSION,
            'time': datetime.datetime.now().isoformat(),
            'mixer': mixer,
            'mixer_input_default_output': mixer_input_default_output,
            'mixer_input_microphone': mixer_input_microphone,
            'virtual_microphone': virtual_microphone},
            f)

    config['microphone'] = microphone['name']
    config['output_monitor'] = output_monitor['name']
    write_config(config)


def stop():
    try:
        with open(SETUP_CONFIG_FILE, 'rt', encoding='utf-8') as f:
            config = json.load(f)
            if config['version'] != SETUP_CONFIG_FILE_VERSION:
                print('Config has wrong version!')
                exit(-1)

            pactl_unload_module(config['virtual_microphone'])
            pactl_unload_module(config['mixer_input_microphone'])
            pactl_unload_module(config['mixer_input_default_output'])
            pactl_unload_module(config['mixer'])
        os.remove(SETUP_CONFIG_FILE)
    except FileNotFoundError:
        pass


def reset():
    subprocess.run(['pulseaudio', '-k'])
    try:
        os.remove(SETUP_CONFIG_FILE)
    except FileNotFoundError:
        pass


def main(command):
    os.makedirs('~/.config/AudioStreamPulse', exist_ok=True)
    if command == 'start':
        start()
    elif command == 'stop':
        stop()
    elif command == 'reset':
        reset()
    else:
        print('Unknown command: ', command)


if __name__ == '__main__':
    main(sys.argv[1])
