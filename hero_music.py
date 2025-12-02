from livekit.agents import function_tool
import webbrowser
import random
import urllib.parse
import logging

@function_tool()
def play_spotify_music(query: str = None):
    """
    Opens Spotify and plays a requested or random trending song.
    """
    try:
        if not query or "random" in query.lower():
            trending_songs = [
                "Calm Down Rema", "As It Was Harry Styles",
                "Blinding Lights The Weeknd", "Flowers Miley Cyrus"
            ]
            song = random.choice(trending_songs)
            logging.info(f"🎵 Playing random trending song: {song}")
        else:
            song = query

        encoded = urllib.parse.quote(song)
        spotify_url = f"https://open.spotify.com/search/{encoded}"
        webbrowser.open(spotify_url)
        return f"Playing {song} on Spotify..."
    except Exception as e:
        logging.error(f"Error playing music: {e}")
        return "Sorry, I couldn’t open Spotify."
