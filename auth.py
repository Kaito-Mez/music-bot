def get_token():
    with open("data/discordToken.txt", "r") as f:
        token = f.readline()
        return token
    
def get_spotify_auth():
    data = []
    with open("./data/spotifyToken.txt", "r") as f:
        data.append(f.readline())

    with open("./data/spotifySecret.txt", "r") as f:
        data.append(f.readline())

    return data

def get_soundcloud_auth():
    with open("./data/soundcloudToken.txt", "r") as f:
        data = f.readline()
    return data