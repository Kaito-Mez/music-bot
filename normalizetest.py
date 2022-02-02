import ffmpeg_normalize

test = ffmpeg_normalize.FFmpegNormalize(audio_codec="mp3", )

test.add_media_file("sound/start.mp3", "sound/start_norm.mp3")

test.run_normalization()



