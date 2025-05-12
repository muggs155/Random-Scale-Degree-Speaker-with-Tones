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

**use of ssml to get /eI/ sound for A -- ```'<speak><phoneme alphabet="ipa" ph="eɪ">A</phoneme></speak>'```**

# Key Features and Notes:

**Scale Degree Normalization: Handles various ways of writing scale degrees (e.g., "flat 3", "b3", "FLAT3" all become "B3").**

**Key and Octave: You specify the root note of the key (C, C#, Db, etc.) and its octave. The tones for the scale degrees will be relative to this root.**

**Tone Duration and Volume: TONE_DURATION_SEC and TONE_AMPLITUDE_FACTOR can be adjusted at the top of the script if needed.**

**Error Handling: Includes checks for missing libraries, invalid keys, and unrecognized scale degrees.**

**Timing: The --delay argument aims for the specified time between the start of one spoken element and the start of the next. The actual time taken for speech is not precisely factored in for simplicity, but the fixed tone duration is.**






python scale_degree_speaker.py "1,3,5,flat 7,2" --key C






>> The user wants a concise summary to recreate the Python script. I should outline the main functionalities, command-line arguments, and core logic of the script based on the provided immersive artifact.

# Project Summary Outline:

## Purpose: Python script that speaks randomly selected musical scale degrees, plays corresponding tones, and speaks the note names, cycling through a list of user-specified keys.
### Core Functionalities:
Text-to-speech for scale degrees and note names.

Tone generation for musical notes.

Parsing of scale degrees (e.g., "1", "flat 3", "b7", "#4").

Calculation of note frequencies based on key and scale degree.

Contextual enharmonic naming (e.g., "E flat" in C for "b3").

Cycling through a list of musical keys.

Controlling the number of times each unique degree is played per key.

Announcing new keys.

Key Libraries: pyttsx3 (TTS), pygame (sound), numpy (audio array manipulation).

### Command-Line Interface:

elements_string: Comma-separated scale degrees.

--key: Comma-separated musical keys.

--plays_per_key: How many times each unique degree is played before switching keys.

--delay: Overall delay between element cycles.

--octave: Octave for the root of the keys.

--tone_name_delay: Delay after tone before speaking its name.
### Workflow:

Initialize TTS and Pygame.

Activate the first key (announce, set root MIDI note, reset play counts).

### Loop:

If current key session is complete (all unique elements played --plays_per_key times):

Switch to the next key.

Activate the new key.

Randomly select an eligible (not yet fully played for this key session) scale degree from the input list.

Speak the scale degree (e.g., "flat 3").

Calculate the MIDI note and frequency for the degree in the current key.

Play the tone.

Wait for tone_name_delay.

Speak the calculated note name (e.g., "E flat"), considering key and degree context for enharmonics.

Update play count for the selected degree in the current key.

Pause to maintain the overall delay.
### Enharmonic/Naming Logic:

normalize_degree_string(): Standardizes input like "flat 3" to "B3".

get_speakable_degree_name(): Converts "B3" to "flat 3" for TTS.

get_note_name_from_midi(): Determines if a note should be named with a sharp or flat based on:

The explicit nature of the original scale degree (e.g., "b3" implies a flat).

The current musical key context (e.g., "F" major or "Db" major prefer flats).



