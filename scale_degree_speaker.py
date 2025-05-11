import argparse
import random
import time
import sys

# Attempt to import required libraries and provide guidance if missing
try:
    import pyttsx3
except ImportError:
    print("ERROR: The 'pyttsx3' library is not installed. Please install it by running: pip install pyttsx3")
    print("You may also need to install OS-specific text-to-speech engines.")
    sys.exit(1)

try:
    import pygame
except ImportError:
    print("ERROR: The 'pygame' library is not installed. Please install it by running: pip install pygame")
    sys.exit(1)

try:
    import numpy
except ImportError:
    print("ERROR: The 'numpy' library is not installed. Please install it by running: pip install numpy")
    sys.exit(1)

# --- Music Theory Constants ---
NOTES_SEMITONES_FROM_C = { # For parsing input key names
    "C": 0, "B#": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "FB": 4, "F": 5, "E#": 5, "F#": 6, "GB": 6, "G": 7,
    "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11, "CB": 11,
}
DEGREE_SEMITONE_INTERVALS = {
    "1": 0, "B2": 1, "2": 2, "B3": 3, "3": 4, "4": 5,
    "B5": 6, "#4": 6, "5": 7, "B6": 8, "#5": 8, "6": 9,
    "B7": 10, "7": 11
}

# Lists for speaking calculated note names, chosen based on key context
SHARP_NOTE_NAMES = [
    "C", "C sharp", "D", "D sharp", "E", "F",
    "F sharp", "G", "G sharp", "A", "A sharp", "B"
]
FLAT_NOTE_NAMES = [
    "C", "D flat", "D", "E flat", "E", "F",
    "G flat", "G", "A flat", "A", "B flat", "B"
]

A4_FREQ = 440.0
A4_MIDI_NOTE = 69
TONE_DURATION_SEC = 0.5
TONE_AMPLITUDE_FACTOR = 0.3
SAMPLE_RATE = 44100
NEW_KEY_ANNOUNCEMENT_DELAY_SEC = 2.0

# --- Text-to-Speech Functions ---
def initialize_tts_engine():
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        print(f"Error initializing text-to-speech engine: {e}\n"
              "Ensure a compatible TTS engine is installed.")
        sys.exit(1)

def speak_text(engine, text):
    if not text or text.isspace():
        print("Skipping empty text for speech.")
        return
    print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()

# --- Tone Generation and Music Logic Functions ---
def normalize_degree_string(degree_str):
    s = degree_str.lower().strip().replace("flat ", "b").replace("flat", "b")
    s = s.replace("sharp ", "#").replace("sharp", "#").replace(" ", "")
    return s.upper()

def get_note_name_from_midi(midi_note_number, key_context_name_str):
    """
    Converts MIDI note to a speakable name (e.g., 'C sharp' or 'D flat'),
    preferring flats for flat keys (like F, Bb, Db) and sharps otherwise.
    Octave is not included.
    """
    if not (0 <= midi_note_number <= 127):
        return "Unknown note"
    
    note_index = midi_note_number % 12
    
    # Determine if the key context suggests using flat names
    # key_context_name_str is the user's input for the current key (e.g., "Db", "F", "C#")
    processed_key_name_for_context_check = key_context_name_str.upper()
    
    use_flats = False
    # Prefer flats if key name itself is 'F' (e.g. "F major")
    if processed_key_name_for_context_check == "F":
        use_flats = True
    # Prefer flats if key name contains 'B' (for flat, e.g., "Db", "Bb")
    # but not 'B#' (which is C, a sharp context by default for C)
    elif 'B' in processed_key_name_for_context_check and "B#" not in processed_key_name_for_context_check:
        use_flats = True
        
    if use_flats:
        return FLAT_NOTE_NAMES[note_index]
    else: # Default to sharps for C, G, D, A, E, B, F#, C# and other contexts
        return SHARP_NOTE_NAMES[note_index]

def calculate_frequency_and_midi(root_key_midi_note, degree_interval_semitones):
    if root_key_midi_note is None or degree_interval_semitones is None:
        return None, None
    target_midi_note = root_key_midi_note + degree_interval_semitones
    if not (0 <= target_midi_note <= 127):
        print(f"Warning: Calculated MIDI note {target_midi_note} is out of range (0-127).")
    frequency = A4_FREQ * (2 ** ((target_midi_note - A4_MIDI_NOTE) / 12.0))
    return frequency, target_midi_note

def generate_sine_wave_array(frequency, duration_sec, num_channels=1):
    t = numpy.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    wave_mono = numpy.sin(frequency * t * 2 * numpy.pi)
    audio_data_mono = (wave_mono * (2**15 - 1) * TONE_AMPLITUDE_FACTOR).astype(numpy.int16)
    if num_channels == 2:
        return numpy.ascontiguousarray(numpy.column_stack((audio_data_mono, audio_data_mono)))
    return audio_data_mono

def play_generated_tone(frequency, duration_sec):
    if frequency is None:
        print("Skipping tone (invalid frequency).")
        return
    print(f"Playing tone: {frequency:.2f} Hz for {duration_sec}s")
    try:
        mixer_status = pygame.mixer.get_init()
        if not mixer_status:
            print("Error: Pygame mixer not initialized for tone playback.")
            return
        mixer_channels = mixer_status[2]
        wave_array = generate_sine_wave_array(frequency, duration_sec, num_channels=mixer_channels)
        sound = pygame.sndarray.make_sound(wave_array)
        sound.play()
        pygame.time.wait(int(duration_sec * 1000))
    except Exception as e:
        print(f"Error playing tone: {e}")

def activate_key(key_name, octave, tts_engine, unique_elements_ref):
    """Announces new key, calculates its root MIDI, and resets play counts."""
    # Use the user-provided key_name for speech
    speak_text(tts_engine, f"New Key: {key_name}") 
    time.sleep(NEW_KEY_ANNOUNCEMENT_DELAY_SEC)
    
    # Use uppercase for dictionary lookup
    key_semitone_offset = NOTES_SEMITONES_FROM_C[key_name.upper()] 
    key_root_midi_note = (octave + 1) * 12 + key_semitone_offset
    
    print(f"Activated Key: {key_name} (Octave {octave}). Root MIDI: {key_root_midi_note}")
    
    element_play_counts = {el: 0 for el in unique_elements_ref}
    return key_root_midi_note, element_play_counts

# --- Main Program ---
def main():
    parser = argparse.ArgumentParser(
        description='Speaks random scale degrees, plays tones, speaks note names (contextually), and cycles through keys.'
    )
    parser.add_argument('elements_string', type=str, help='Comma-separated scale degrees (e.g., "1,flat 3,5").')
    parser.add_argument('--key', type=str, required=True, help='Comma-separated musical keys (e.g., "C,Db,F#").')
    parser.add_argument('--plays_per_key', type=int, default=1, help='Times each unique degree is played per key before switching (min 1, default: 1).')
    parser.add_argument('--delay', type=float, default=3.0, help='Approx. delay (s) between element cycles (default: 3.0).')
    parser.add_argument('--octave', type=int, default=4, help='Octave for key roots (e.g., 4 for C4, default: 4).')
    parser.add_argument('--tone_name_delay', type=float, default=1.0, help='Delay (s) after tone before speaking its name (default: 1.0).')
    args = parser.parse_args()

    if args.tone_name_delay < 0: args.tone_name_delay = 0.0
    if args.plays_per_key < 1: args.plays_per_key = 1
    if args.delay < 0: args.delay = 0.0

    elements_list_raw = [elem.strip() for elem in args.elements_string.split(',') if elem.strip()]
    if not elements_list_raw:
        print("Error: No valid elements in elements_string."); sys.exit(1)
    unique_elements = sorted(list(set(elements_list_raw)))
    print(f"Unique scale degrees to be practiced: {unique_elements}")

    # Keep original casing for announcements, use .upper() for logic/lookups
    key_strings_input_original_case = [k.strip() for k in args.key.split(',') if k.strip()]
    if not key_strings_input_original_case:
        print("Error: No valid keys provided in --key argument."); sys.exit(1)
    
    for k_str_orig in key_strings_input_original_case:
        if k_str_orig.upper() not in NOTES_SEMITONES_FROM_C:
            print(f"Error: Invalid key '{k_str_orig}' in key list. Valid options include: {', '.join(NOTES_SEMITONES_FROM_C.keys())}")
            sys.exit(1)
    
    print(f"Key sequence: {key_strings_input_original_case}")
    print(f"Plays per unique element per key: {args.plays_per_key}")
    # ... (rest of the print statements from before)

    tts_engine = initialize_tts_engine()
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        mixer_status = pygame.mixer.get_init()
        if not mixer_status:
            print("CRITICAL ERROR: Pygame mixer failed to initialize."); sys.exit(1)
        print(f"Pygame mixer: Freq={mixer_status[0]}, Format={mixer_status[1]}, Channels={mixer_status[2]}")
    except Exception as e:
        print(f"Error initializing Pygame: {e}"); sys.exit(1)

    current_key_idx = 0
    # Use original case key name for context and announcements
    current_key_name_original_case = key_strings_input_original_case[current_key_idx] 
    current_key_root_midi_note, element_play_counts_for_current_key = activate_key(
        current_key_name_original_case, args.octave, tts_engine, unique_elements
    )

    try:
        print(f"\nStarting practice. Press Ctrl+C to stop.")
        while True:
            num_elements_fully_played_this_key_session = sum(
                1 for el in unique_elements if element_play_counts_for_current_key.get(el, 0) >= args.plays_per_key
            )

            if num_elements_fully_played_this_key_session == len(unique_elements):
                print(f"\n--- Key '{current_key_name_original_case}' session complete. ---")
                current_key_idx = (current_key_idx + 1) % len(key_strings_input_original_case)
                current_key_name_original_case = key_strings_input_original_case[current_key_idx]
                current_key_root_midi_note, element_play_counts_for_current_key = activate_key(
                    current_key_name_original_case, args.octave, tts_engine, unique_elements
                )
                print(f"--- Continuing with new key: {current_key_name_original_case} ---")
                continue

            eligible_elements_to_play = [
                el for el in unique_elements if element_play_counts_for_current_key.get(el, 0) < args.plays_per_key
            ]
            if not eligible_elements_to_play:
                print("Error: No eligible elements to play logic error."); time.sleep(1); continue 

            selected_element_text = random.choice(eligible_elements_to_play)
            
            print(f"\nNext element for key {current_key_name_original_case}: '{selected_element_text}'")
            speak_text(tts_engine, selected_element_text)
            
            normalized_degree = normalize_degree_string(selected_element_text)
            frequency_to_play, target_midi_note_played = None, None
            time_spent_on_audio_events = 0.0

            if normalized_degree in DEGREE_SEMITONE_INTERVALS:
                degree_interval = DEGREE_SEMITONE_INTERVALS[normalized_degree]
                frequency_to_play, target_midi_note_played = calculate_frequency_and_midi(
                    current_key_root_midi_note, degree_interval
                )
            else:
                print(f"Warning: Scale degree '{selected_element_text}' (norm: '{normalized_degree}') not recognized.")

            if frequency_to_play is not None:
                play_generated_tone(frequency_to_play, TONE_DURATION_SEC)
                time_spent_on_audio_events += TONE_DURATION_SEC

                if target_midi_note_played is not None:
                    # Pass the original case key name for context
                    note_name_to_speak = get_note_name_from_midi(target_midi_note_played, current_key_name_original_case)
                    time.sleep(args.tone_name_delay)
                    time_spent_on_audio_events += args.tone_name_delay
                    speak_text(tts_engine, note_name_to_speak)
            
            element_play_counts_for_current_key[selected_element_text] = \
                element_play_counts_for_current_key.get(selected_element_text, 0) + 1
            
            print(f"Element '{selected_element_text}' play count for key {current_key_name_original_case}: "
                  f"{element_play_counts_for_current_key[selected_element_text]}/{args.plays_per_key}")

            sleep_for = args.delay - time_spent_on_audio_events
            if sleep_for > 0:
                time.sleep(sleep_for)
            elif args.delay < time_spent_on_audio_events and time_spent_on_audio_events > 0:
                print(f"Warning: Target cycle delay ({args.delay}s) < time for audio events "
                      f"({time_spent_on_audio_events:.2f}s).")
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Exiting program.")
        pygame.quit()

if __name__ == "__main__":
    main()

