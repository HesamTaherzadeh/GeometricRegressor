#!/bin/bash

# Check if ffmpeg and ImageMagick (convert) are installed
if ! command -v ffmpeg &> /dev/null || ! command -v convert &> /dev/null
then
    echo "Error: ffmpeg and/or ImageMagick are not installed. Please install them."
    exit 1
fi

# Loop through all MKV files in the current directory
for video in *.mkv; do
    # Check if there are any MKV files
    if [ ! -f "$video" ]; then
        echo "No MKV files found in the current directory."
        exit 1
    fi

    # Get the base name of the file (without extension)
    base_name=$(basename "$video" .mkv)

    echo "Processing $video..."

    # Create a folder to store frames
    mkdir -p "$base_name-frames"

    # Extract frames using ffmpeg (no resizing, full quality, keeping original resolution)
    ffmpeg -i "$video" -vf "fps=10" "$base_name-frames/frame_%04d.png"

    # Process frames in smaller batches to avoid memory exhaustion
    batch_size=50  # Number of frames per batch
    total_frames=$(ls "$base_name-frames/frame_*.png" | wc -l)
    for ((i=1; i<=total_frames; i+=batch_size)); do
        # Process each batch of frames
        batch_start=$i
        batch_end=$((i + batch_size - 1))
        batch_frames=$(seq -f "$base_name-frames/frame_%04g.png" $batch_start $batch_end)

        # Convert current batch to a temporary GIF
        convert -delay 10 -loop 0 -quality 100 $batch_frames temp_batch.gif

        # Append the current batch to the final GIF
        if [ -f "$base_name.gif" ]; then
            convert "$base_name.gif" temp_batch.gif -append "$base_name.gif"
        else
            mv temp_batch.gif "$base_name.gif"
        fi
    done

    # Remove the frames folder after GIF creation
    rm -r "$base_name-frames"

    echo "$video converted to $base_name.gif"
done

echo "All MKV files have been processed."

