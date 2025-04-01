import datetime
import os
import subprocess
import sgtk

INPUT_PROFILES = {'none': [],
                  'standard': ['-gamma', '2.2'],
                  'exr32_Rec709_gamma2.4': ['-gamma', '2.4', '-colorspace', 'bt709', '-color_trc',
                                            'iec61966-2-1']
                  }


logger = sgtk.platform.get_logger(__name__)

def sequence_transcode(fileName, pathToImageSequence, outputFilePath, frame_rate=25):
    # pathToImageSequence example --> publishToCloudTestAsset_scene_persp.v020.%04d.png
    # Finds the start frame of the sequence based off the file path
    imageFileBaseName = os.path.basename(os.path.splitext(pathToImageSequence)[0])[:-5]
    listOfImages = os.listdir(os.path.dirname(pathToImageSequence))
    for i in sorted(listOfImages):
        if i.startswith(imageFileBaseName):
            startFrame = os.path.splitext(i)[0][-4:]
            break
    else:
        raise Exception('There was a problem transcoding')

    logger.info("Transcode operation - sequence_transcode")

    fontSize = 38
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')
    logoPath = os.path.join(current_dir, '422Logo.png')
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(
        ':', '\:')
    # fontPath requires some weird formatting to work inside subprocess for ffmpeg.exe
    # The : needs to be escaped, no other backslashes can be present

    cmdLineArray = [ffmpegPath, '-r', str(frame_rate), '-start_number', startFrame, '-gamma', '2.2', '-i', pathToImageSequence,
         '-i', logoPath,
         '-filter_complex',
         "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
         "drawtext=fontsize=" + str(fontSize) + ":x=10:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + fileName.replace('_Tags.mp4', '') + "',"
                                                                                                                                                           "drawtext=fontsize=" + str(fontSize) + ":x=w-tw-125:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + "'Frame'" + "',"
                                                                                                                                                                                                                                                                                           "drawtext=fontsize=" + str(fontSize) + ":x=w-105:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text=%{n}:start_number=1",
         '-pix_fmt', 'yuv420p',
                    '-b:v', '30000k', outputFilePath, '-y', '-fps_mode', 'passthrough']

    do_ffmpeg(cmdLineArray)
    return

def video_transcode_audio(fileName, pathToImageSequence, outputFilePath, audio_file, audio_start, start_frame, duration,
                          frame_rate=25, input_profile='standard'):
    if input_profile not in INPUT_PROFILES.keys():
        raise Exception('Input profile not supported')
    fontSize = 38
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')
    logoPath = os.path.join(current_dir, '422Logo.png')
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(':', '\:')

    logger.info("Transcode operation - video_transcode_audio")

    # fontPath requires some weird formatting to work inside subprocess for ffmpeg.exe
    # The : needs to be escaped, no other backslashes can be present
    if float(start_frame) - float(audio_start) < 0:
        audioStartTime = '-0' + str(
            datetime.timedelta(seconds=(abs(float(start_frame) - float(audio_start))) / float(frame_rate)))
    else:
        audioStartTime = '0' + str(
            datetime.timedelta(seconds=(float(start_frame) - float(audio_start)) / float(frame_rate)))

    audioDuration = '0' + str(datetime.timedelta(seconds=(duration / float(frame_rate))))

    # jim - mix in a silent stream of audio to prevent audio slippage when publishing to SG
    audioSlipSpit = audioStartTime.split(":")
    audioSlipSec = audioSlipSpit[2]
    audioDelay = int(float(float(audioSlipSec) * float(frame_rate)) * ((1 / float(frame_rate)) * 1000))

    cmdLineArray = ([ffmpegPath, '-v', 'debug',
                     '-r', str(frame_rate)]
                    + INPUT_PROFILES[input_profile]
                    + ['-i', pathToImageSequence,
                       '-i', logoPath,
                       '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', '-t', '10',
                       '-i', audio_file,
                       '-filter_complex',
                       '[3]adelay=' + str(audioDelay) + '|' + str(audioDelay) + '[a2];[2][a2]amix=inputs=2:duration=longest[a]', '-map', '[a]',
                       '-filter_complex',
                       "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
                       "drawtext=fontsize=" + str(fontSize) + ":x=10:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + fileName.replace('_Tags.mp4', '') + "',"
                                                                                                                                                                         "drawtext=fontsize=" + str(fontSize) + ":x=w-tw-120:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + "'Frame'" + "',"
                                                                                                                                                                                                                                                                                                         "drawtext=fontsize=" + str(fontSize) + ":x=w-110:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text=%{n}:start_number=1",
                       '-pix_fmt', 'yuv420p',
                       '-b:v', '30000k', '-to', audioDuration, outputFilePath, '-y', '-fps_mode', 'passthrough'])

    extension = pathToImageSequence.split('.')[-1]
    if extension and extension.lower() in ['tif', 'tiff']:
        cmdLineArray = ([ffmpegPath, '-r', str(frame_rate)]
                        + INPUT_PROFILES[input_profile] +
                        ['-i', pathToImageSequence,
                        '-i', logoPath,
                         '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', '-t', '10',
                        '-i', audio_file,
                        '-filter_complex',
                         '[2]adelay=' + str(audioDelay) + '|' + str(audioDelay) + '[a2];[3][a2]amix=inputs=2:duration=longest[a]', '-map', '[a]',
                        '-filter_complex',
                        "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
                        "drawtext=fontsize=" + str(fontSize) + ":x=10:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + fileName.replace('_Tags.mp4', '') + "',"
                                                                                                                                                                          "drawtext=fontsize=" + str(fontSize) + ":x=w-tw-120:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + "'Frame'" + "',"
                                                                                                                                                                                                                                                                                                          "drawtext=fontsize=" + str(fontSize) + ":x=w-110:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text=%{n}:start_number=1",
                        '-pix_fmt', 'yuv420p',
                        '-b:v', '30000k', '-to', audioDuration, outputFilePath, '-y', '-fps_mode', 'passthrough'])

    do_ffmpeg(cmdLineArray)
    return

def video_transcode(fileName, pathToImageSequence, outputFilePath, frame_rate=25, input_profile='standard'):
    if input_profile not in INPUT_PROFILES.keys():
        raise Exception('Input profile not supported')
    fontSize = 38
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')
    logoPath = os.path.join(current_dir, '422Logo.png')
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(
        ':', '\:')

    logger.info("Transcode operation - video_transcode")

    # fontPath requires some weird formatting to work inside subprocess for ffmpeg.exe
    # The : needs to be escaped, no other backslashes can be present
    cmdLineArray = [ffmpegPath, '-r', str(frame_rate)] + INPUT_PROFILES[input_profile] + ['-i', pathToImageSequence, '-i', logoPath,
                 '-filter_complex',
                 "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
                 "drawtext=fontsize=" + str(fontSize) + ":x=10:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + fileName.replace('_Tags.mp4', '') + "',"
                                                                                                                                                                   "drawtext=fontsize=" + str(fontSize) + ":x=w-tw-120:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + "'Frame'" + "',"
                                                                                                                                                                                                                                                                                                   "drawtext=fontsize=" + str(fontSize) + ":x=w-110:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text=%{n}:start_number=1",
                 '-pix_fmt', 'yuv420p',
                 '-b:v', '30000k', outputFilePath, '-y', '-fps_mode', 'passthrough']

    extension = pathToImageSequence.split('.')[-1]
    if extension and extension.lower() in ['tif', 'tiff']:
        cmdLineArray = [ffmpegPath, '-r', str(frame_rate)] + INPUT_PROFILES[input_profile] + ['-i', pathToImageSequence, '-i', logoPath,
                     '-filter_complex',
                     "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
                     "drawtext=fontsize=" + str(fontSize) + ":x=10:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + fileName.replace('_Tags.mp4', '') + "',"
                                                                                                                                                                       "drawtext=fontsize=" + str(fontSize) + ":x=w-tw-120:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + "'Frame'" + "',"
                                                                                                                                                                                                                                                                                                       "drawtext=fontsize=" + str(fontSize) + ":x=w-110:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text=%{n}:start_number=1",
                     '-pix_fmt', 'yuv420p',
                     '-b:v', '30000k', outputFilePath, '-y', '-fps_mode', 'passthrough']

    do_ffmpeg(cmdLineArray)
    return

def sequence_transcode_withoutTags(pathToImageSequence, outputFilePath, startFrame, playblastFileName,
                                   extraMessage='',
                                   frame_rate=25):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')

    extraMessage = extraMessage.replace(":", "|")

    logger.info("Transcode operation - sequence_transcode_withoutTags")

    fontSize = 38
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(
        ':', '\:')
    cmdLineArray = [ffmpegPath, '-r', str(frame_rate), '-start_number', startFrame, '-i', pathToImageSequence,
               '-filter_complex',
                    "drawtext=fontsize=" + str(fontSize) + ":x=(w-text_w)/2:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + playblastFileName + "',"
                                                                                                                                                                "drawtext=fontsize=" + str(fontSize - 2) + ":x=(w-text_w)/2:y=10:fontcolor=White:fontfile='" + fontPath + "':text='" + extraMessage + "'",
               '-pix_fmt', 'yuv420p',
               '-b:v', '30000k', outputFilePath, '-y', '-fps_mode', 'passthrough']

    do_ffmpeg(cmdLineArray)
    return

def sequence_transcode_withoutTags_withAudio(pathToImageSequence, outputFilePath, startFrame, endFrame, frameOffset,
                                             playblastFileName, audioFile, extraMessage='', frame_rate=25,
                                             input_profile='standard'):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')

    fontSize = 38
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(
        ':', '\:')

    logger.info("Transcode operation - sequence_transcode_withoutTags_withAudio")

    # Appending a '0' at the start because ffmpeg needs the format to be 00:00:00 and timedelta does 0:00:00
    # Yes this will break if someone tries to playblast something longer than 9.9 hours - Unlikely but not impossible

    # If statement with the '-0' is because timedelta doesn't support negative values and instead shows "-1 Day 23:55:59"
    # which completely breaks ffmpeg. I use abs() to make the negative time positive then add a - manually.

    if float(startFrame) - float(frameOffset) < 0:
        audioStartTime = '-0' + str(
            datetime.timedelta(seconds=(abs(float(startFrame) - float(frameOffset))) / float(frame_rate)))
    else:
        audioStartTime = '0' + str(
            datetime.timedelta(seconds=(float(startFrame) - float(frameOffset)) / float(frame_rate)))

    audioDuration = '0' + str(datetime.timedelta(seconds=(float(endFrame) - float(startFrame)) / float(frame_rate)))

    # jim - mix in a silent stream of audio to prevent audio slippage when publishing to SG
    audioSlipSpit = audioStartTime.split(":")
    audioSlipSec = audioSlipSpit[2]
    audioDelay = int(float(float(audioSlipSec) * float(frame_rate)) * ((1 / float(frame_rate)) * 1000))

    extraMessage = extraMessage.replace(":", "|")

    cmdLineArray = [ffmpegPath, '-v', 'debug',
                    '-r', str(frame_rate), '-start_number', startFrame,
                    '-i', pathToImageSequence,
                    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', '-t', '10',
                    '-i', audioFile,
                    '-filter_complex',
                    '[2]adelay=' + str(audioDelay) + '|' + str(audioDelay) + '[a2];[1][a2]amix=inputs=2:duration=longest[a]', '-map', '[a]',
                    '-filter_complex',
                    "drawtext=fontsize=" + str(fontSize) + ":x=(w-text_w)/2:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + playblastFileName + "',"
                                                                                                                                                                "drawtext=fontsize=" + str(fontSize - 2) + ":x=(w-text_w)/2:y=10:fontcolor=White:fontfile='" + fontPath + "':text='" + extraMessage + "'",
                    '-pix_fmt', 'yuv420p',
                    '-b:v', '30000k', '-to', audioDuration, outputFilePath, '-y', '-fps_mode', 'passthrough']

    do_ffmpeg(cmdLineArray)
    return

def image_transcode_withTags(inputImage, outputImage, burnIns, extraMsg):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ffmpegPath = os.path.join(current_dir, 'ffmpeg.exe')

    extraMsg = extraMsg.replace(":", "|")

    logger.info("Transcode operation - image_transcode_withTags")

    fontSize = 18
    fontPath = os.path.join(current_dir, 'Moderat-Regular.otf').replace('\\', '/').replace(
        ':', '\:')
    logoPath = os.path.join(current_dir, '422Logo.png')

    cmdLineArray = [ffmpegPath, '-i', inputImage, '-i', logoPath,
                     '-filter_complex',
                     "[0:v][1:v]overlay=(main_w-overlay_w)-10:10,"
                     "drawtext=fontsize=" + str(fontSize - 2) + ":x=(w-text_w)/2:y=10:fontcolor=White:fontfile='" + fontPath + "':text='" + extraMsg + "',"
                                                                                                                                                       "drawtext=fontsize=" + str(fontSize) + ":x=(w-text_w)/2:y=h-th-10:fontcolor=White:fontfile='" + fontPath + "':text='" + burnIns + "'",
                     '-pix_fmt', 'yuv420p',
                    outputImage, '-y', '-fps_mode', 'passthrough']

    do_ffmpeg(cmdLineArray)
    return


def do_ffmpeg(cmdLineArray):
    # these lines are here to help debug ffmpeg esp for afx un comment to enable output to the logger
    # cmdLine = " ".join(cmdLineArray)
    # logger.info("cmdLine - " +cmdLine)
    # for i in range(0, len(cmdLineArray)):
    #     logger.info("cmdLine - " + str(i) +" - " +cmdLineArray[i])

    result = subprocess.run(cmdLineArray, capture_output=True, text=True)
    logger.info(result.stderr)

    if result.returncode != 0:
        raise (Exception('ffmpeg command failed'))
    return