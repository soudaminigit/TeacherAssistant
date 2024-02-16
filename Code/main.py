import asyncio
import threading
import os
import pyttsx3
from moviepy.editor import AudioFileClip, concatenate_audioclips, CompositeVideoClip, TextClip, ImageClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from openai import AsyncOpenAI
from moviepy.config import change_settings
from moviepy.video.tools.subtitles import TextClip

from openai import AsyncOpenAI

async def request_openai():
    # Set your OpenAI API key
    api_key = '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'

    # Create an instance of AsyncOpenAI with the API key
    client = AsyncOpenAI(api_key=api_key)

    # Make an asynchronous request
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an instructor teaching in a formal tone."},
            {"role": "user",
             "content": "Create a 10-seconds video script on the introduction of Machine Learning. Make it a dialog between two people: Teacher and Student. The dialog sentences should be short and crisp."},
        ],
        temperature=0.5,
        max_tokens=1024
    )

    # Print a focused subset of information for inspection
    print("Response choices:", response.choices)
    print("Selected content:", response.choices[0].message.content)

    return response.choices[0].message.content

# Run the event loop to await the asynchronous call
loop = asyncio.get_event_loop()
generated_content = loop.run_until_complete(request_openai())

# Process the generated content
dialogue_lines = generated_content.split('\n')

student_dialogues = []
teacher_dialogues = []
current_speaker = None

for line in dialogue_lines:
    if line.startswith("Student:"):
        current_speaker = "Student"
        student_dialogues.append(line[len("Student:"):].strip())
    elif line.startswith("Teacher:"):
        current_speaker = "Teacher"
        teacher_dialogues.append(line[len("Teacher:"):].strip())
    elif current_speaker:
        # If the line doesn't start with "Student:" or "Teacher:" but we have a current speaker
        if current_speaker == "Student":
            student_dialogues[-1] += " " + line.strip()
        elif current_speaker == "Teacher":
            teacher_dialogues[-1] += " " + line.strip()

# Create a directory to store individual audio files
output_dir = "audio_files"
os.makedirs(output_dir, exist_ok=True)

def generate_audio(text, output_path, is_student=True):
    def thread_function():
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            voice1 = voices[1].id  # Voice for students
            voice2 = voices[0].id  # Voice for teachers

            engine.setProperty('rate', 150)

            if is_student:
                engine.setProperty('voice', voice1)
            else:
                engine.setProperty('voice', voice2)

            engine.save_to_file(text, output_path)
            engine.runAndWait()
            print(f"Audio generated: {output_path}")
        except Exception as e:
            print(f"Error generating audio: {e}")
            raise  # Reraise the exception for better debugging

    # Create a thread and run the text-to-speech conversion in the background
    thread = threading.Thread(target=thread_function)
    thread.start()
    thread.join()

# Generate audio files for student dialogues
for index, student_line in enumerate(student_dialogues):
    student_audio_path = os.path.join(output_dir, f"student_{index}.mp3")
    generate_audio(student_line, student_audio_path, is_student=True)

# Generate audio files for teacher dialogues
for index, teacher_line in enumerate(teacher_dialogues):
    teacher_audio_path = os.path.join(output_dir, f"teacher_{index}.mp3")
    generate_audio(teacher_line, teacher_audio_path, is_student=False)

print("Audio files generated for student and teacher lines.")

# Get the list of student and teacher audio files
student_audio_files = [os.path.join(output_dir, f"student_{index}.mp3") for index in range(len(student_dialogues))]
teacher_audio_files = [os.path.join(output_dir, f"teacher_{index}.mp3") for index in range(len(teacher_dialogues))]

# Print the lists for debugging
print("Student audio files:", student_audio_files)
print("Teacher audio files:", teacher_audio_files)

# Specify the output path for the combined audio
combined_audio_output_path = "combined_audio.mp3"

# Check if there are audio files to combine for students and teachers
if student_audio_files and teacher_audio_files:
    # Combine audio files for students and teachers
    def combine_audio_files(output_path, student_files, teacher_files):
        student_clips = [AudioFileClip(file) for file in student_files]
        teacher_clips = [AudioFileClip(file) for file in teacher_files]

        # Check if there are audio clips to combine
        if student_clips and teacher_clips:
            # Interleave student and teacher audio clips to simulate a conversation
            interleaved_clips = [clip for pair in zip(teacher_clips, student_clips) for clip in pair]

            # Print the number of interleaved clips for debugging
            print("Number of interleaved clips:", len(interleaved_clips))

            # Concatenate interleaved audio clips
            combined_audio = concatenate_audioclips(interleaved_clips)

            # Print the duration of the combined audio for debugging
            print("Combined audio duration:", combined_audio.duration)

            # Export the combined audio to a single MP3 file
            combined_audio.write_audiofile(output_path, codec='mp3')

            print(f"Combined audio exported to: {output_path}")
        else:
            print("No audio files to combine.")

    combine_audio_files(combined_audio_output_path, student_audio_files, teacher_audio_files)
else:
    print("No audio files to combine.")

# Check if the combined audio file exists before trying to load it
if os.path.exists(combined_audio_output_path):
    # Load combined audio file
    combined_audio_clip = AudioFileClip(combined_audio_output_path)

    # Print the duration of the combined audio for debugging
    print("Combined audio duration:", combined_audio_clip.duration)

    # Specify the path to ImageMagick binary
    change_settings({'IMAGEMAGICK_BINARY': r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe'})

    # Create a directory to store individual video files
    output_video_dir = "video_files"
    os.makedirs(output_video_dir, exist_ok=True)

    # ... (previous code)

    # Set the desired width and height for the video
    width, height = 1920, 1080

    # Initialize current_time outside the loops
    current_time_student = 0
    current_time_teacher = 0

    # Set text position
    #text_position = ('center', height - 50)
    #
    #
    # Adjust the vertical position as needed

    # Generate video clips for students
    for student_index, (line, duration) in enumerate(zip(student_dialogues, [15] * len(student_dialogues))):
        student_image_path = 'student_gen.png'  # Provide the actual path for student image

        # Load the corresponding student audio clip
        student_audio_path = os.path.join(output_dir, f"student_{student_index}.mp3")
        student_audio_clip = AudioFileClip(student_audio_path)

        # Adjust audio volume to match student speaking volume
        student_audio_clip = student_audio_clip.volumex(0.5)  # Adjust the volume factor as needed

        # Create video clip with student image and audio
        current_time_student = 0
        video_clip_student = ImageClip(student_image_path, duration=duration)
        video_clip_student = video_clip_student.subclip(current_time_student, current_time_student + duration)
        video_clip_student = video_clip_student.set_audio(student_audio_clip)

        # Add text to the video clip
        text_student = line.split(".")
        #text_lines = list( line )
        #length=len(tline)
        # Split by 30 chars
        #no_of_lines=length//30+1
        line1=text_student[0]
        #cur_line=0
        font_size=8
        font_color='Red'
        font_name='Keep-Calm-Medium'
        #while(cur_line<length):
            #next_line=cur_line+30
        screensize = (1000,500)
        #txt_clip_student = TextClip(line1, fontsize=font_size, color=font_color,kerning=-2, interline=-1, size = 
#screensize,method='Caption').set_position(('right', 'bottom')).set_duration(student_audio_clip.duration).set_start(3)
        txt_clip_student = TextClip(line, fontsize=font_size, color=font_color, method='Caption',align='center').set_position(('left', 'center')).set_duration(student_audio_clip.duration)
            #set_position(('right', 'bottom'))
            #cur_line=next_line

        video_clip_student = CompositeVideoClip([video_clip_student, txt_clip_student])

        # Set the duration manually
        # Set the duration based on the audio clip duration
        video_clip_student = video_clip_student.set_duration(student_audio_clip.duration)

        # Export the video clip with combined audio, subtitles, and image
        output_video_path_student = os.path.join(output_video_dir, f"student_video_{student_index}.mp4")
        video_clip_student.write_videofile(output_video_path_student, fps=10, codec='libx264', audio_codec='aac',
                                           threads=8)

        print(f"Student Video exported to: {output_video_path_student}")

        current_time_student += duration

    # Generate video clips for teachers
    for teacher_index, (line, duration) in enumerate(zip(teacher_dialogues, [25] * len(teacher_dialogues))):
        teacher_image_path = 'teacher_gen.png'  # Provide the actual path for teacher image

        # Load the corresponding teacher audio clip
        teacher_audio_path = os.path.join(output_dir, f"teacher_{teacher_index}.mp3")
        teacher_audio_clip = AudioFileClip(teacher_audio_path)

        # Adjust audio volume to match teacher speaking volume
        teacher_audio_clip = teacher_audio_clip.volumex(0.5)  # Adjust the volume factor as needed

        # Create video clip with teacher image and audio
        current_time_teacher=0
        video_clip_teacher = ImageClip(teacher_image_path, duration=duration)
        video_clip_teacher = video_clip_teacher.subclip(current_time_teacher, current_time_teacher + duration)
        video_clip_teacher = video_clip_teacher.set_audio(teacher_audio_clip)

        # Add text to the video clip
        text_teacher = f"Teacher:{teacher_index + 1}: {line}"
        txt_clip_teacher = TextClip(line, fontsize=font_size, color=font_color,method='Caption',align='center').set_position(('left', 'center')).set_duration(teacher_audio_clip.duration)

        video_clip_teacher = CompositeVideoClip([video_clip_teacher, txt_clip_teacher])

        # Set the duration manually
        # Set the duration based on the audio clip duration
        video_clip_teacher = video_clip_teacher.set_duration(teacher_audio_clip.duration)

        # Export the video clip with combined audio, subtitles, and image
        output_video_path_teacher = os.path.join(output_video_dir, f"teacher_video_{teacher_index}.mp4")
        video_clip_teacher.write_videofile(output_video_path_teacher, fps=10, codec='libx264', audio_codec='aac',
                                           threads=8)

        print(f"Teacher Video exported to: {output_video_path_teacher}")

        current_time_teacher += duration




    output_video_dir = "video_files"
    teacher_video_paths = [os.path.join(output_video_dir, f"teacher_video_{i}.mp4") for i in range(6)]
    student_video_paths = [os.path.join(output_video_dir, f"student_video_{i}.mp4") for i in range(6)]

    # Combine teacher and student video paths
    all_video_paths = sorted(list(zip(teacher_video_paths, student_video_paths)))

    # Concatenate video clips in the desired order
    concatenated_clips = []
    for teacher_path, student_path in all_video_paths:
        teacher_clip = VideoFileClip(teacher_path)
        student_clip = VideoFileClip(student_path)

        # Assuming teacher and student clips have the same duration, adjust as needed
        concatenated_clip = concatenate_videoclips([teacher_clip, student_clip])

        concatenated_clips.append(concatenated_clip)

    # Export the final concatenated video
    final_output_path = os.path.join(output_video_dir, "final_output.mp4")
    final_clip = concatenate_videoclips(concatenated_clips)
    final_clip.write_videofile(final_output_path, fps=10, codec='libx264', audio_codec='aac', threads=8)
    final_clip.ipython_display(width = 280,fps=16)
    print(f"Final concatenated video exported to: {final_output_path}")
