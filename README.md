# Audio Stream Pulse

Simple Python script to create a new virtual microphone that mixes the audio from your microphone with the output audio. This allows to stream audio on Linux to applications like Discord or Zoom.

This script also doesn't have the issue that you can hear yourself. It properly keeps the audio apart and only provides both to the new virtual microphone that can be used in Discord or Zoom.

## Requirements

* PulseAudio
* Python 3.8
* Tested it on XUbuntu 20.04

## Installation

I'd recommend, git checkout this somewhere in your home folder. And then create a soft-link to it in `~/bin`:

`ln -s ~/bin/AudioStreamPulse <Project Location>/main.py`

## Usage

* Start: `AudioStreamPulse start`
* Stop: `AudioStreamPulse stop`
* Reset: `AudioStreamPulse reset`

## Config

By default, it will store the last used devices in `~/.config/AudioStreamPulse/config.json`. In addition, the currently in-use setup is stored in `/tmp/audiostreampulse.json`. Those paths can be adjusted in `main.py`.