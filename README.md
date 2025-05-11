# Random-Scale-Degree-Speaker-with-Tones
Music Practice Utility: Says random note degrees, along with the tone for that degree.

Intended to allow a musician to practice playing scale degrees relative to a given key note. 

This is an AI generated file from Gemini 2.5 pro (preview), as an experiment in quickly generating a practical (?) utility. My guestimate is this would have easily taken me 1-4 days between library research and trying/testing. It was functional in under an hour with Gemini.

pip install pyttsx3 pygame numpy


# command line options
```
usage: scale_degree_speaker.py [-h] --key KEY [--plays_per_key PLAYS_PER_KEY]
                               [--delay DELAY] [--octave OCTAVE]
                               [--tone_name_delay TONE_NAME_DELAY]
                               elements_string

Speaks random scale degrees, plays tones, speaks note names (contextually), and cycles
through keys.

positional arguments:
  elements_string       Comma-separated scale degrees (e.g., "1,flat 3,5").

options:
  -h, --help            show this help message and exit
  --key KEY             Comma-separated musical keys (e.g., "C,Db,F#").
  --plays_per_key PLAYS_PER_KEY
                        Times each unique degree is played per key before switching (min
                        1, default: 1).
  --delay DELAY         Approx. delay (s) between element cycles (default: 3.0).
  --octave OCTAVE       Octave for key roots (e.g., 4 for C4, default: 4).
  --tone_name_delay TONE_NAME_DELAY
                        Delay (s) after tone before speaking its name (default: 1.0).
 ```
# TODO
**When speaking note name after a tone, sometimes the enharmonic is used. Seems to be in the get_note_name_from_midi(). Trying to work out dialog.**
**Need to gather ALL the dialogs with Gemini and update this readme.**

# Key Features and Notes:

**Scale Degree Normalization: Handles various ways of writing scale degrees (e.g., "flat 3", "b3", "FLAT3" all become "B3").**

**Key and Octave: You specify the root note of the key (C, C#, Db, etc.) and its octave. The tones for the scale degrees will be relative to this root.**

**Tone Duration and Volume: TONE_DURATION_SEC and TONE_AMPLITUDE_FACTOR can be adjusted at the top of the script if needed.**

**Error Handling: Includes checks for missing libraries, invalid keys, and unrecognized scale degrees.**

**Timing: The --delay argument aims for the specified time between the start of one spoken element and the start of the next. The actual time taken for speech is not precisely factored in for simplicity, but the fixed tone duration is.**






python scale_degree_speaker.py "1,3,5,flat 7,2" --key C

# Dialog with Gemini
>>
create python code that will "speak" randomly selected elements from a command line provided string. 
The string elements will be comma separated. 
For example the string might contain "1,2,flat 3,4,5,flat 6,flat 7". 
The elements must be spoken about 3 seconds apart.
-----
Okay, I can help you create a Python script that does just that! This script will take a comma-separated string of items from the command line, then randomly select and "speak" these items one by one, with a pause of about 3 seconds between each.

To make this work, the script will use a text-to-speech library called pyttsx3. You'll need to install it if you haven't already. You can usually install it by running:
pip install pyttsx3

Depending on your operating system, pyttsx3 might also require other system libraries for speech synthesis (e.g., espeak on Linux, SAPI5 on Windows, NSSpeechSynthesizer on macOS). If you encounter issues, the pyttsx3 documentation or error messages should guide you.


>>
Each element of the string is a scale degree. 
The key of the scale will be provided on the command line. 
A tone must be produced after each spoken element, relative to the provided key.
-----
Okay, I've updated the Python script to meet your new requirements. Here's what's changed:

Musical Key Input: The script now requires a --key command-line argument (e.g., --key C, --key F#, --key Bb) to specify the musical key.
Tone Generation: After each scale degree is spoken, the script will generate and play a corresponding musical tone.
The tone's pitch is calculated relative to the provided key and the spoken scale degree (e.g., if the key is C and "3" is spoken, an E note will be played).
It uses pygame for sound generation, so you'll need to install it along with numpy: pip install pyttsx3 pygame numpy
Scale Degree Parsing: The input elements are now interpreted as musical scale degrees (e.g., "1", "flat 3", "5", "sharp 4"). The script normalizes these inputs (handles "flat", "sharp", "b", "#", and spacing) to determine the correct musical interval.
Updated Dependencies: The script now explicitly checks for pygame and numpy in addition to pyttsx3 at startup.
Tone Duration: A constant TONE_DURATION_SEC (defaulting to 0.5 seconds) defines how long each tone plays. The delay between spoken elements now accounts for this tone duration to maintain the desired overall timing.
