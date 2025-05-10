import argparse
import random
import time
import sys

# Attempt to import required libraries and provide guidance if missing
try:
    import pyttsx3
except ImportError:
    print("ERROR: The 'pyttsx3' library is not installed.")
    print("Please install it by running: pip install pyttsx3")
    print("You may also need to install OS-specific text-to-speech engines.")
    print("E.g., on Debian/Ubuntu: sudo apt-get install espeak")
    print("E.g., on Fedora: sudo dnf install espeak")
    sys.exit(1)

try:
    import pygame
except ImportError:
    print("ERROR: The 'pygame' library is not installed.")
    print("Please install it by running: pip install pygame")
    sys.exit(1)

try:
    import numpy
except ImportError:
    print("ERROR: The 'numpy' library is not installed.")
    print("Please install it by running: pip install numpy")
    sys.exit(1)

# --- Music Theory Constants ---
# Note names to their semitone offset from C. Includes common enharmonics.
NOTES_SEMITONES_FROM_C = {
    "C": 0, "B#": 0,
    "C#": 1, "DB": 1,
    "D": 2,
    "D#": 3, "EB": 3,
    "E": 4, "FB": 4,
    "F": 5, "E#": 5,
    "F#": 6, "GB": 6,
    "G": 7,
    "G#": 8, "AB": 8,
    "A": 9,
    "A#": 10, "BB": 10,
    "B": 11, "CB": 11,
}

# Scale degree names (normalized) to their interval in semitones from the root of the scale.
DEGREE_SEMITONE_INTERVALS = {
    "1": 0,    # Unison
    "B2": 1,   # Minor 2nd / Flat 2
    "2": 2,    # Major 2nd
    "B3": 3,   # Minor 3rd / Flat 3
    "3": 4,    # Major 3rd
    "4": 5,    # Perfect 4th
    "B5": 6,   # Diminished 5th / Flat 5
    "#4": 6,   # Augmented 4th / Sharp 4
    "5": 7,    # Perfect 5th
    "B6": 8,   # Minor 6th / Flat 6
    "#5": 8,   # Augmented 5th / Sharp 5
    "6": 9,    # Major 6th
    "B7": 10,  # Minor 7th / Flat 7
    "7": 11    # Major 7th
}

A4_FREQ = 440.0  # Frequency of A4 note (standard tuning)
A4_MIDI_NOTE = 69  # MIDI note number for A4
MIDDLE_C_MIDI_NOTE = 60 # MIDI note number for C4 (octave 4)

TONE_DURATION_SEC = 0.5  # Duration of the generated tone in seconds
TONE_AMPLITUDE_FACTOR = 0.3 # Volume of the tone (0.0 to 1.0)
SAMPLE_RATE = 44100 # Audio sample rate in Hz

# --- Text-to-Speech Functions ---
def initialize_tts_engine():
    """Initializes and returns the text-to-speech engine."""
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        print(f"Error initializing text-to-speech engine: {e}")
        print("Ensure a compatible TTS engine (SAPI5, NSSpeechSynthesizer, espeak) is installed.")
        sys.exit(1)

def speak_text(engine, text):
    """Uses the TTS engine to speak the given text."""
    if not text or text.isspace():
        print("Skipping empty element for speech.")
        return
    print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()

# --- Tone Generation Functions ---
def normalize_degree_string(degree_str):
    """
    Normalizes a scale degree string to a standard format.
    Example: 'flat 3' -> 'B3', 'Sharp 4' -> '#4', '1' -> '1'
    """
    s = degree_str.lower().strip()
    s = s.replace("flat ", "b").replace("flat", "b")
    s = s.replace("sharp ", "#").replace("sharp", "#")
    s = s.replace(" ", "")  # Remove any remaining spaces
    return s.upper() # Standardize to uppercase for dictionary keys

def calculate_frequency(root_key_midi_note, degree_interval_semitones):
    """
    Calculates the frequency of a note given a root MIDI note and an interval.
    Args:
        root_key_midi_note: MIDI note number of the key's root (e.g., C4).
        degree_interval_semitones: Interval in semitones from the root.
    Returns:
        Frequency in Hz, or None if calculation is not possible.
    """
    if root_key_midi_note is None or degree_interval_semitones is None:
        return None
    target_midi_note = root_key_midi_note + degree_interval_semitones
    frequency = A4_FREQ * (2 ** ((target_midi_note - A4_MIDI_NOTE) / 12.0))
    return frequency

def generate_sine_wave_array(frequency, duration_sec, sample_rate=SAMPLE_RATE, amplitude_factor=TONE_AMPLITUDE_FACTOR, num_channels=1):
    """
    Generates a sine wave as a NumPy array for pygame.
    Args:
        frequency (float): Frequency of the sine wave in Hz.
        duration_sec (float): Duration of the wave in seconds.
        sample_rate (int): Samples per second.
        amplitude_factor (float): Scales amplitude (0.0 to 1.0).
        num_channels (int): Number of audio channels (1 for mono, 2 for stereo).
    Returns:
        numpy.ndarray: 16-bit integer array representing the sine wave.
                       Shape is (samples,) for mono, (samples, 2) for stereo.
    """
    t = numpy.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    wave_mono = numpy.sin(frequency * t * 2 * numpy.pi)
    # Scale to 16-bit integer range and apply amplitude factor
    audio_data_mono = (wave_mono * (2**15 - 1) * amplitude_factor).astype(numpy.int16)

    if num_channels == 2:
        # Convert mono to stereo by duplicating the channel
        # Resulting shape: (number_of_samples, 2)
        audio_data_stereo = numpy.ascontiguousarray(numpy.column_stack((audio_data_mono, audio_data_mono)))
        return audio_data_stereo
    elif num_channels == 1:
        return audio_data_mono
    else:
        # Fallback or error for unexpected channel count
        print(f"Warning: Unsupported number of channels ({num_channels}) requested for wave generation. Defaulting to mono.")
        return audio_data_mono


def play_generated_tone(frequency, duration_sec):
    """Plays a tone of a given frequency and duration using pygame."""
    if frequency is None:
        print("Skipping tone generation (invalid frequency).")
        return
    
    print(f"Playing tone: {frequency:.2f} Hz for {duration_sec}s")
    try:
        mixer_init_status = pygame.mixer.get_init()
        if not mixer_init_status:
            print("Error: Pygame mixer not initialized when trying to play tone.")
            return

        mixer_channels = mixer_init_status[2] # Index 2 is channels
        
        wave_array = generate_sine_wave_array(frequency, duration_sec, num_channels=mixer_channels)
        
        sound = pygame.sndarray.make_sound(wave_array)
        sound.play()
        pygame.time.wait(int(duration_sec * 1000))  # Wait for sound to finish
    except Exception as e:
        print(f"Error playing tone: {e}")

# --- Main Program ---
def main():
    """Main function to parse arguments, select, speak elements, and play tones."""
    parser = argparse.ArgumentParser(
        description='Speaks randomly selected scale degrees from a comma-separated string and plays corresponding tones.'
    )
    parser.add_argument(
        'elements_string',
        type=str,
        help='A comma-separated string of scale degrees (e.g., "1,flat 3,5,sharp 4").'
    )
    parser.add_argument(
        '--key',
        type=str,
        required=True,
        help='The musical key (e.g., C, G#, Bb, F). Case-insensitive.'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='Approximate delay in seconds between the start of speaking one element and the start of the next (default: 3.0).'
    )
    parser.add_argument(
        '--octave',
        type=int,
        default=4,
        help='The octave for the root note of the key (e.g., 4 for C4, default: 4).'
    )

    args = parser.parse_args()

    elements_input = args.elements_string
    delay_seconds = args.delay
    key_name_input = args.key.upper()
    root_octave = args.octave

    if key_name_input not in NOTES_SEMITONES_FROM_C:
        print(f"Error: Invalid musical key '{args.key}'. Valid examples: C, F#, Bb.")
        print(f"Available root notes: {', '.join(NOTES_SEMITONES_FROM_C.keys())}")
        sys.exit(1)

    if not elements_input:
        print("Error: The elements string cannot be empty.")
        sys.exit(1)

    elements_list = [elem.strip() for elem in elements_input.split(',')]
    elements_list = [elem for elem in elements_list if elem] 

    if not elements_list:
        print("Error: No valid elements found in the provided string after parsing.")
        sys.exit(1)

    print(f"Parsed scale degrees: {elements_list}")
    print(f"Key: {key_name_input}, Root Octave: {root_octave}")
    print(f"Target interval between spoken elements: {delay_seconds}s (includes tone duration of {TONE_DURATION_SEC}s)")

    tts_engine = initialize_tts_engine()

    try:
        # Attempt to initialize mixer with mono, but we'll adapt if it ends up stereo
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512) 
        pygame.init() 
        
        mixer_status = pygame.mixer.get_init()
        if not mixer_status:
            print("CRITICAL ERROR: Pygame mixer failed to initialize.")
            sys.exit(1)
        print(f"Pygame mixer initialized with: Frequency={mixer_status[0]}, Format={mixer_status[1]}, Channels={mixer_status[2]}")

    except Exception as e:
        print(f"Error initializing Pygame mixer: {e}")
        sys.exit(1)
    
    key_semitone_offset_from_c = NOTES_SEMITONES_FROM_C[key_name_input]
    c_in_target_octave_midi = 12 * (root_octave + 1)
    key_root_midi_note = c_in_target_octave_midi + key_semitone_offset_from_c
    
    print(f"Root MIDI note for {key_name_input}{root_octave} calculated as: {key_root_midi_note}")

    try:
        print(f"Starting. Press Ctrl+C to stop.")
        while True:
            selected_element_text = random.choice(elements_list)
            
            speak_text(tts_engine, selected_element_text)
            
            normalized_degree = normalize_degree_string(selected_element_text)
            
            frequency_to_play = None
            if normalized_degree in DEGREE_SEMITONE_INTERVALS:
                degree_interval = DEGREE_SEMITONE_INTERVALS[normalized_degree]
                frequency_to_play = calculate_frequency(key_root_midi_note, degree_interval)
            else:
                print(f"Warning: Scale degree '{selected_element_text}' (normalized to '{normalized_degree}') not recognized. Cannot play tone.")

            if frequency_to_play is not None:
                play_generated_tone(frequency_to_play, TONE_DURATION_SEC)
            
            sleep_for = delay_seconds - TONE_DURATION_SEC
            if frequency_to_play is None: 
                sleep_for = delay_seconds

            if sleep_for > 0:
                time.sleep(sleep_for)
            elif delay_seconds < TONE_DURATION_SEC and frequency_to_play is not None:
                print(f"Warning: Target delay ({delay_seconds}s) is less than tone duration ({TONE_DURATION_SEC}s). Effective delay will be ~{TONE_DURATION_SEC}s.")
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Exiting program.")
        pygame.quit()

if __name__ == "__main__":
    main()
