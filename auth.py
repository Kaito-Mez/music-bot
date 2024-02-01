def get_token():
    with open("data/discordToken.txt", "r") as f:
        token = f.readline()
        return token