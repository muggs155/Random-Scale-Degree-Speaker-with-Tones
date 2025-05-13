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
# For parsing input root note names
ROOT_NOTES_SEMITONES_FROM_C = {
    "C": 0, "B#": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "FB": 4, "F": 5, "E#": 5, "F#": 6, "GB": 6, "G": 7,
    "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11, "CB": 11,
}
# Scale degrees and their intervals in semitones from the root
DEGREE_SEMITONE_INTERVALS = {
    "1": 0,
    "B2": 1, "2": 2,
    "B3": 3, "3": 4,
    "4": 5,
    "B5": 6, "#4": 6, "5": 7,
    "B6": 8, "#5": 8, "6": 9,
    "B7": 10, "7": 11,
    # Extended degrees
    "B9": 13, "9": 14, "#9": 15, # Minor, Major, Augmented 9th
    "11": 17, "#11": 18,          # Perfect, Augmented 11th
    "B13": 20, "13": 21           # Minor, Major 13th
}

# Lists for speaking calculated note names. "A" is " A " for /eI/ pronunciation.
SHARP_NOTE_NAMES = [
    "C", "C sharp", "D", "D sharp", "E", "F",
    "F sharp", "G", "G sharp", " A ", " A sharp", "B"
]
FLAT_NOTE_NAMES = [
    "C", "D flat", "D", "E flat", "E", "F",
    "G flat", "G", " A flat", " A ", "B flat", "B"
]

A4_FREQ = 440.0  # Standard A4 pitch
A4_MIDI_NOTE = 69 # MIDI note number for A4
TONE_DURATION_SEC = 0.5
TONE_AMPLITUDE_FACTOR = 0.3
SAMPLE_RATE = 44100
NEW_ROOT_NOTE_ANNOUNCEMENT_DELAY_SEC = 2.0

# --- Text-to-Speech Functions ---
def initialize_tts_engine():
    """Initializes and returns the text-to-speech engine."""
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        print(f"Error initializing text-to-speech engine: {e}\n"
              "Ensure a compatible TTS engine is installed.")
        sys.exit(1)

def speak_text(engine, text):
    """Uses the TTS engine to speak the given text."""
    if not text or text.isspace():
        print("Skipping empty text for speech.")
        return
    print(f"Speaking: {text}")
    engine.say(text)
    engine.runAndWait()

# --- Tone Generation and Music Logic Functions ---
def normalize_degree_string(degree_str):
    """Converts various degree inputs to a standard internal format (e.g., 'flat 3' -> 'B3', '9' -> '9')."""
    s = degree_str.lower().strip()
    s = s.replace("flat ", "b").replace("flat", "b")
    s = s.replace("sharp ", "#").replace("sharp", "#")
    s = s.replace(" ", "")  # Remove any remaining spaces
    # For numbers, ensure they are uppercase if they became so (e.g. from "B3")
    # but keep simple numbers like "9", "11", "13" as is.
    if not s.isnumeric() and (s.startswith('B') or s.startswith('#')):
        return s.upper()
    return s.upper() # Generally make uppercase for consistency in dictionary keys

def get_speakable_degree_name(degree_str_as_input):
    """Converts an input degree string (e.g., 'b3', '#11', '9') to a speakable format (e.g., 'flat 3', 'sharp 11', '9')."""
    # Use the normalized internal format to decide prefix, but original number part for speech
    # E.g. "b9" -> "flat 9", "#11" -> "sharp 11", "7" -> "7"
    
    temp_normalized = degree_str_as_input.lower().strip() # Work with a temporary version
    
    number_part = ""
    prefix = ""

    if temp_normalized.startswith("flat ") or temp_normalized.startswith("b"):
        prefix = "flat "
        number_part = temp_normalized.replace("flat ", "").replace("b", "")
    elif temp_normalized.startswith("sharp ") or temp_normalized.startswith("#"):
        prefix = "sharp "
        number_part = temp_normalized.replace("sharp ", "").replace("#", "")
    else: # Natural degree
        number_part = temp_normalized
        
    number_part = number_part.strip() # Clean up number part

    if prefix:
        return prefix + number_part
    return number_part # Return original number if no prefix

def get_note_name_from_midi(midi_note_number, root_note_context_str, original_degree_str):
    """
    Converts MIDI note to a speakable name, considering root note context and original degree.
    Octave is not included. Uses "Ay" for "A".
    """
    if not (0 <= midi_note_number <= 127):
        return "Unknown note"
    
    note_index = midi_note_number % 12
    
    normalized_original_degree = normalize_degree_string(original_degree_str)
    processed_root_note_context = root_note_context_str.upper()
    
    use_flats_due_to_root = False
    if processed_root_note_context == "F":
        use_flats_due_to_root = True
    elif 'B' in processed_root_note_context and "B#" not in processed_root_note_context : # Db, Eb, Gb, Ab, Bb
        use_flats_due_to_root = True
        
    final_use_flats = use_flats_due_to_root # Default to root context
    if normalized_original_degree.startswith('B'): # Degree is explicitly flat (e.g., "b3", "b9")
        final_use_flats = True
    elif normalized_original_degree.startswith('#'): # Degree is explicitly sharp (e.g., "#4", "#11")
        final_use_flats = False
        
    if final_use_flats:
        return FLAT_NOTE_NAMES[note_index]
    else:
        return SHARP_NOTE_NAMES[note_index]

def calculate_frequency_and_midi(root_note_midi, degree_interval_semitones):
    """Calculates frequency and target MIDI note from a root MIDI and interval."""
    if root_note_midi is None or degree_interval_semitones is None:
        return None, None
    target_midi_note = root_note_midi + degree_interval_semitones
    if not (0 <= target_midi_note <= 127): # Check MIDI range
        print(f"Warning: Calculated MIDI note {target_midi_note} is out of standard range (0-127).")
    frequency = A4_FREQ * (2 ** ((target_midi_note - A4_MIDI_NOTE) / 12.0))
    return frequency, target_midi_note

def generate_sine_wave_array(frequency, duration_sec, num_channels=1):
    """Generates a sine wave NumPy array, adaptable for mono or stereo."""
    t = numpy.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    wave_mono = numpy.sin(frequency * t * 2 * numpy.pi) # Mono wave
    # Scale to 16-bit integer range and apply amplitude factor
    audio_data_mono = (wave_mono * (2**15 - 1) * TONE_AMPLITUDE_FACTOR).astype(numpy.int16)

    if num_channels == 2: # If stereo output is needed
        # Duplicate mono channel to create stereo
        return numpy.ascontiguousarray(numpy.column_stack((audio_data_mono, audio_data_mono)))
    return audio_data_mono # Return mono array

def play_generated_tone(frequency, duration_sec):
    """Plays a tone of a given frequency and duration using pygame."""
    if frequency is None:
        print("Skipping tone generation (invalid frequency).")
        return
    
    print(f"Playing tone: {frequency:.2f} Hz for {duration_sec}s")
    try:
        mixer_status = pygame.mixer.get_init() # Get current mixer settings
        if not mixer_status:
            print("Error: Pygame mixer not initialized when trying to play tone.")
            return

        mixer_channels = mixer_status[2] # Actual number of channels mixer is using
        wave_array = generate_sine_wave_array(frequency, duration_sec, num_channels=mixer_channels)
        
        sound = pygame.sndarray.make_sound(wave_array)
        sound.play()
        pygame.time.wait(int(duration_sec * 1000))  # Wait for sound to finish
    except Exception as e:
        print(f"Error playing tone: {e}")

def activate_root_note(root_note_name, octave, tts_engine, unique_elements_ref):
    """Announces new root note, calculates its root MIDI, and resets play counts."""
    speak_text(tts_engine, f"New Root Note: {root_note_name}") 
    time.sleep(NEW_ROOT_NOTE_ANNOUNCEMENT_DELAY_SEC)
    
    # Use uppercase for dictionary lookup of semitone offset
    root_note_semitone_offset = ROOT_NOTES_SEMITONES_FROM_C[root_note_name.upper()] 
    # Calculate the MIDI note for the root in the specified octave
    # MIDI C0=12, C1=24, ... C4 (Middle C)=60. Formula: (octave + 1) * 12
    current_root_midi_note = (octave + 1) * 12 + root_note_semitone_offset
    
    print(f"Activated Root Note: {root_note_name} (Octave {octave}). Root MIDI: {current_root_midi_note}")
    
    # Reset play counts for each unique element for this new root note session
    element_play_counts = {el: 0 for el in unique_elements_ref}
    return current_root_midi_note, element_play_counts

# --- Main Program ---
def main():
    parser = argparse.ArgumentParser(
        description='Speaks random scale degrees, plays tones, speaks note names (contextually), and cycles through root notes.'
    )
    parser.add_argument('elements_string', type=str, help='Comma-separated scale degrees (e.g., "1,flat 3,5,b9,#11").')
    parser.add_argument('--root_notes', type=str, required=True, help='Comma-separated musical root notes (e.g., "C,Db,F#").')
    parser.add_argument('--plays_per_root', type=int, default=1, help='Times each unique degree is played per root note before switching (min 1, default: 1).')
    parser.add_argument('--delay', type=float, default=3.0, help='Approx. delay (s) between element cycles (default: 3.0).')
    parser.add_argument('--octave', type=int, default=4, help='Octave for root notes (e.g., 4 for C4, default: 4).')
    parser.add_argument('--tone_name_delay', type=float, default=1.0, help='Delay (s) after tone before speaking its name (default: 1.0).')
    args = parser.parse_args()

    # Validate numerical arguments
    if args.tone_name_delay < 0: args.tone_name_delay = 0.0
    if args.plays_per_root < 1: args.plays_per_root = 1
    if args.delay < 0: args.delay = 0.0

    # Parse and validate elements string
    elements_list_raw_input = [elem.strip() for elem in args.elements_string.split(',') if elem.strip()]
    if not elements_list_raw_input:
        print("Error: No valid elements in elements_string."); sys.exit(1)
    # unique_elements_as_input stores the exact strings from user input for tracking plays
    unique_elements_as_input = sorted(list(set(elements_list_raw_input)))
    print(f"Unique scale degrees to be practiced (as input): {unique_elements_as_input}")

    # Parse and validate root notes, keeping original casing for announcements
    root_notes_input_original_case = [rn.strip() for rn in args.root_notes.split(',') if rn.strip()]
    if not root_notes_input_original_case:
        print("Error: No valid root notes provided in --root_notes argument."); sys.exit(1)
    
    for rn_str_orig in root_notes_input_original_case:
        if rn_str_orig.upper() not in ROOT_NOTES_SEMITONES_FROM_C:
            print(f"Error: Invalid root note '{rn_str_orig}' in list. Valid options include: {', '.join(ROOT_NOTES_SEMITONES_FROM_C.keys())}")
            sys.exit(1)
    
    print(f"Root note sequence: {root_notes_input_original_case}")
    print(f"Plays per unique element per root note: {args.plays_per_root}")
    print(f"Root note octave: {args.octave}")
    print(f"Overall cycle delay: {args.delay}s, Tone duration: {TONE_DURATION_SEC}s, Note name speech delay: {args.tone_name_delay}s")


    tts_engine = initialize_tts_engine()
    try:
        # Initialize Pygame mixer, try for mono but adapt if stereo
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512) 
        pygame.init() # Initializes all pygame modules
        mixer_status = pygame.mixer.get_init() # Check actual mixer settings
        if not mixer_status:
            print("CRITICAL ERROR: Pygame mixer failed to initialize."); sys.exit(1)
        print(f"Pygame mixer initialized with: Frequency={mixer_status[0]}, Format={mixer_status[1]}, Channels={mixer_status[2]}")
    except Exception as e:
        print(f"Error initializing Pygame: {e}"); sys.exit(1)

    current_root_note_idx = 0
    # Use original case root note name for context and announcements
    current_root_note_original_case = root_notes_input_original_case[current_root_note_idx] 
    # Initial root note activation
    current_root_midi_note, element_play_counts_for_current_root = activate_root_note(
        current_root_note_original_case, args.octave, tts_engine, unique_elements_as_input
    )

    try:
        print(f"\nStarting practice. Press Ctrl+C to stop.")
        while True:
            # Check if current root note's practice session is complete
            num_elements_fully_played_this_session = sum(
                1 for el in unique_elements_as_input if element_play_counts_for_current_root.get(el, 0) >= args.plays_per_root
            )

            if num_elements_fully_played_this_session == len(unique_elements_as_input):
                print(f"\n--- Root Note '{current_root_note_original_case}' session complete. ---")
                current_root_note_idx = (current_root_note_idx + 1) % len(root_notes_input_original_case)
                current_root_note_original_case = root_notes_input_original_case[current_root_note_idx]
                current_root_midi_note, element_play_counts_for_current_root = activate_root_note(
                    current_root_note_original_case, args.octave, tts_engine, unique_elements_as_input
                )
                print(f"--- Continuing with new root note: {current_root_note_original_case} ---")
                continue # Restart loop for the new root note

            # Select an element that still needs to be played for the current root note session
            eligible_elements_to_play = [
                el for el in unique_elements_as_input if element_play_counts_for_current_root.get(el, 0) < args.plays_per_root
            ]
            if not eligible_elements_to_play: # Should not happen if logic is correct
                print("Error: No eligible elements to play, but root note switch condition not met. This may indicate a logic error."); time.sleep(1); continue 

            selected_element_text_as_input = random.choice(eligible_elements_to_play) # This is the original string like "b3" or "flat 9"
            
            # For speaking the degree itself, get its human-friendly name
            speakable_degree_name = get_speakable_degree_name(selected_element_text_as_input)
            print(f"\nNext element for root {current_root_note_original_case}: '{selected_element_text_as_input}' (spoken as '{speakable_degree_name}')")
            speak_text(tts_engine, speakable_degree_name) # 1. Speak scale degree
            
            # For internal logic and tone calculation, use the normalized version of the degree
            normalized_degree_for_logic = normalize_degree_string(selected_element_text_as_input)
            
            frequency_to_play, target_midi_note_played = None, None
            time_spent_on_audio_events = 0.0 # Track time for tone + note name speech

            if normalized_degree_for_logic in DEGREE_SEMITONE_INTERVALS:
                degree_interval = DEGREE_SEMITONE_INTERVALS[normalized_degree_for_logic]
                frequency_to_play, target_midi_note_played = calculate_frequency_and_midi(
                    current_root_midi_note, degree_interval
                )
            else:
                # This case should ideally be caught by validating elements_string against DEGREE_SEMITONE_INTERVALS at startup
                print(f"Warning: Scale degree '{selected_element_text_as_input}' (normalized to '{normalized_degree_for_logic}') not recognized in intervals dict.")

            # 2. Play tone (if valid)
            if frequency_to_play is not None:
                play_generated_tone(frequency_to_play, TONE_DURATION_SEC)
                time_spent_on_audio_events += TONE_DURATION_SEC

                # 3. Wait, then speak note name (if tone was played)
                if target_midi_note_played is not None:
                    note_name_to_speak = get_note_name_from_midi(
                        target_midi_note_played, 
                        current_root_note_original_case, # Pass root note for context
                        selected_element_text_as_input # Pass original degree string for context
                    )
                    time.sleep(args.tone_name_delay) # Wait before speaking note name
                    time_spent_on_audio_events += args.tone_name_delay
                    speak_text(tts_engine, note_name_to_speak) # 4. Speak note name
            
            # Update play count for the selected unique element in the current root note's session
            element_play_counts_for_current_root[selected_element_text_as_input] = \
                element_play_counts_for_current_root.get(selected_element_text_as_input, 0) + 1
            
            print(f"Element '{selected_element_text_as_input}' play count for root {current_root_note_original_case}: "
                  f"{element_play_counts_for_current_root[selected_element_text_as_input]}/{args.plays_per_root}")

            # 5. Calculate sleep time to maintain overall delay for the element cycle
            # args.delay is the target time from the start of this cycle to the start of the next.
            sleep_for = args.delay - time_spent_on_audio_events
            
            if sleep_for > 0:
                time.sleep(sleep_for)
            elif args.delay < time_spent_on_audio_events and time_spent_on_audio_events > 0: # Only warn if audio events actually happened
                print(f"Warning: Target cycle delay ({args.delay}s) is less than time taken for audio events "
                      f"({time_spent_on_audio_events:.2f}s). Effective delay will be longer.")
            
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Exiting program.")
        pygame.quit()

if __name__ == "__main__":
    main()


