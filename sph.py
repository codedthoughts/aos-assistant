from pocketsphinx import LiveSpeech		
		
def listen():		
	for phrase in LiveSpeech():
		print(phrase)
		return
listen()
