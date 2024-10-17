# split_wav.py

from pydub import AudioSegment
import os
import sys

def split_wav(file_path, output_dir=None):
    """
    Splits a WAV file into two equal halves.

    :param file_path: Path to the input WAV file.
    :param output_dir: Directory to save the split files. Defaults to the input file's directory.
    """
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    # Load the audio file
    audio = AudioSegment.from_wav(file_path)
    duration_ms = len(audio)  # Duration in milliseconds

    # Calculate midpoint
    midpoint = duration_ms // 2

    # Split the audio
    first_half = audio[:midpoint]
    second_half = audio[midpoint:]

    # Prepare output directory
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    else:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # Generate output file names
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    first_half_path = os.path.join(output_dir, f"{base_name}_part1.wav")
    second_half_path = os.path.join(output_dir, f"{base_name}_part2.wav")

    # Export split files
    first_half.export(first_half_path, format="wav")
    second_half.export(second_half_path, format="wav")

    print(f"Successfully split '{file_path}' into:")
    print(f" - {first_half_path}")
    print(f" - {second_half_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_wav.py <path_to_wav_file> [output_directory]")
    else:
        wav_file = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else None
        split_wav(wav_file, output_directory)